from django.db import models
from core.models import FileAsset, PublishedModel, Technology


class TrainingCategory(PublishedModel):
    name = models.CharField("nombre", max_length=140, unique=True)
    slug = models.SlugField("identificador en URL", max_length=150, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta(PublishedModel.Meta):
        verbose_name = "área temática"
        verbose_name_plural = "áreas temáticas"

    def __str__(self):
        return self.name


class TrainingService(PublishedModel):
    class Icon(models.TextChoices):
        AI = "ai", "Inteligencia artificial"
        CHART = "chart", "Análisis de datos"
        CODE = "code", "Programación"
        DATABASE = "database", "Bases de datos"
        SHIELD = "shield", "Seguridad"
        DESKTOP = "desktop", "Herramientas TI"
        BOOK = "book", "Educación"

    name = models.CharField("nombre", max_length=160)
    slug = models.SlugField("identificador", unique=True, max_length=170)
    category = models.ForeignKey(TrainingCategory, verbose_name="área temática", on_delete=models.PROTECT, related_name="services")
    summary = models.CharField("resumen de la tarjeta", max_length=280)
    description = models.TextField("descripción ampliada", blank=True)
    icon = models.CharField("ícono", choices=Icon.choices, max_length=20, default=Icon.BOOK)
    image = models.ForeignKey(FileAsset, verbose_name="imagen opcional", null=True, blank=True, on_delete=models.PROTECT)
    technologies = models.ManyToManyField(Technology, verbose_name="tecnologías relacionadas", blank=True, related_name="services")

    class Meta(PublishedModel.Meta):
        verbose_name = "servicio de capacitación"
        verbose_name_plural = "servicios de capacitación"

    def __str__(self):
        return self.name
