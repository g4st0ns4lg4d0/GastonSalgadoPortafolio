from pathlib import Path
import re
import uuid
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

from .storage import private_storage
from .validators import validate_upload
from .images import optimize_image


class TimestampedModel(models.Model):
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        abstract = True


class PublishedModel(TimestampedModel):
    position = models.PositiveIntegerField("orden", default=0, help_text="Los números menores aparecen primero.")
    is_published = models.BooleanField("publicado", default=False)

    class Meta:
        abstract = True
        ordering = ["position", "pk"]


class SingletonModel(TimestampedModel):
    """Un registro global, también a nivel de restricción de base de datos."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


def asset_path(instance, filename):
    return f"assets/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class FileAsset(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("título público", max_length=160)
    file = models.FileField("archivo privado", storage=private_storage, upload_to=asset_path, validators=[validate_upload], help_text="PDF, JPG, PNG o WebP, hasta 8 MB. No subas originales con datos sensibles.")
    alt_text = models.CharField("descripción accesible de la imagen", max_length=250, blank=True)
    license = models.CharField("licencia o condiciones de uso", max_length=250, blank=True)
    public_copy_confirmed = models.BooleanField("he revisado y autorizado esta versión pública", default=False, help_text="Confirma derechos de uso y ausencia de RUT, firmas, códigos privados u otros datos sensibles. La revisión es manual.")
    is_public = models.BooleanField("acceso público autorizado", default=False)

    class Meta:
        verbose_name = "archivo y permiso de publicación"
        verbose_name_plural = "archivos y permisos de publicación"
        ordering = ["-created_at"]
        constraints = [models.CheckConstraint(condition=models.Q(is_public=False) | models.Q(public_copy_confirmed=True), name="public_asset_requires_review")]

    def clean(self):
        super().clean()
        if self.is_public and not self.public_copy_confirmed:
            raise ValidationError({"is_public": "Revisa y autoriza primero una copia sin datos sensibles."})
        if self.is_public and self.is_image and not self.alt_text.strip():
            raise ValidationError({"alt_text": "Describe la imagen para que sea accesible."})

    def save(self, *args, **kwargs):
        new_upload = self.file and not self.file._committed
        if new_upload and type(self).objects.filter(pk=self.pk).exists():
            # La autorización pertenece a una versión concreta del documento.
            # Reemplazarlo requiere revisar y autorizar en un guardado posterior.
            self.is_public = False
            self.public_copy_confirmed = False
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"file", "is_public", "public_copy_confirmed"}
        self.clean()
        if new_upload:
            validate_upload(self.file)
            if self.is_image:
                self.file = optimize_image(self.file)
        super().save(*args, **kwargs)

    @property
    def is_image(self):
        return Path(self.file.name).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}

    @property
    def public_url(self):
        return reverse("core:asset", args=[self.pk]) if self.is_public and self.public_copy_confirmed else ""

    def __str__(self):
        return self.title


class Profile(SingletonModel):
    full_name = models.CharField("nombre completo", max_length=160)
    professional_title = models.CharField("título profesional", max_length=160)
    headline = models.CharField("titular de presentación", max_length=200)
    introduction = models.TextField("presentación breve")
    biography_technology = models.TextField("trayectoria tecnológica", blank=True)
    biography_teaching = models.TextField("trayectoria docente", blank=True)
    teaching_methodology = models.TextField("metodología de enseñanza", blank=True)
    location = models.CharField("ubicación", max_length=160, blank=True)
    coverage = models.CharField("cobertura", max_length=200, blank=True)
    email = models.EmailField("correo de contacto")
    whatsapp = models.CharField("WhatsApp", max_length=25, blank=True, validators=[RegexValidator(r"^\+?[0-9 ()-]{8,25}$", "Escribe el número internacional, por ejemplo +56 9 3069 8473.")])
    linkedin_url = models.URLField("LinkedIn", blank=True)
    photo = models.ForeignKey(FileAsset, verbose_name="fotografía profesional", null=True, blank=True, on_delete=models.PROTECT, related_name="profile_photos")
    resume = models.ForeignKey(FileAsset, verbose_name="currículum público en PDF", null=True, blank=True, on_delete=models.PROTECT, related_name="profile_resumes")
    is_published = models.BooleanField("perfil publicado", default=False)

    class Meta:
        verbose_name = "perfil profesional"
        verbose_name_plural = "perfil profesional"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="single_profile")]

    def clean(self):
        super().clean()
        if self.photo and not self.photo.is_image:
            raise ValidationError({"photo": "Selecciona una imagen JPG, PNG o WebP."})
        if self.resume and Path(self.resume.file.name).suffix.lower() != ".pdf":
            raise ValidationError({"resume": "Selecciona un documento PDF."})

    @property
    def whatsapp_url(self):
        digits = re.sub(r"\D", "", self.whatsapp)
        if not digits:
            return ""
        return f"https://wa.me/{digits}?{urlencode({'text': 'Hola Gastón, me gustaría conversar sobre una capacitación para mi equipo.'})}"

    @property
    def photo_public_url(self):
        return self.photo.public_url if self.photo_id and self.photo.is_image else ""

    @property
    def resume_public_url(self):
        return self.resume.public_url if self.resume_id and Path(self.resume.file.name).suffix.lower() == ".pdf" else ""

    def __str__(self):
        return self.full_name


class SiteConfiguration(SingletonModel):
    site_name = models.CharField("nombre del sitio", max_length=120, default="Gastón Salgado")
    seo_title = models.CharField("título para buscadores", max_length=160)
    seo_description = models.CharField("descripción para buscadores", max_length=300)

    class Meta:
        verbose_name = "configuración general"
        verbose_name_plural = "configuración general"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="single_site_configuration")]

    def __str__(self):
        return self.site_name


class Organization(TimestampedModel):
    name = models.CharField("nombre", max_length=200, unique=True)
    website = models.URLField("sitio web", blank=True)
    logo = models.ForeignKey(FileAsset, verbose_name="logotipo", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Technology(PublishedModel):
    class Group(models.TextChoices):
        LANGUAGE = "language", "Lenguajes"
        FRAMEWORK = "framework", "Frameworks"
        DATABASE = "database", "Bases de datos"
        TOOL = "tool", "Herramientas"
        INFRASTRUCTURE = "infrastructure", "Infraestructura"
        TEACHING = "teaching", "Docencia"

    name = models.CharField("nombre", max_length=100, unique=True)
    group = models.CharField("grupo", max_length=20, choices=Group.choices)

    class Meta(PublishedModel.Meta):
        verbose_name = "tecnología o competencia"
        verbose_name_plural = "tecnologías y competencias"

    def __str__(self):
        return self.name
