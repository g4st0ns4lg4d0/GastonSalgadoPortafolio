"""Pruebas de publicación, permisos y edición de la primera etapa."""
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import FileAsset, Profile, SiteConfiguration
from .validators import validate_upload


def png_upload(name="fotografia.png"):
    image = BytesIO()
    Image.new("RGB", (32, 32), color="#2563eb").save(image, format="PNG")
    return SimpleUploadedFile(name, image.getvalue(), content_type="image/png")


def profile_data(**overrides):
    data = {
        "full_name": "Gastón Nicolás Salgado Jara",
        "professional_title": "Ingeniero en Informática",
        "headline": "Formación tecnológica aplicada",
        "introduction": "Docencia y desarrollo de software.",
        "email": "gastonsalgadoj@gmail.com",
        "is_published": True,
    }
    data.update(overrides)
    return data


class HomePublicationTests(TestCase):
    def test_home_works_before_initial_data_import(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Descargar currículum")

    def test_only_published_profile_is_public_and_admin_changes_appear(self):
        profile = Profile.objects.create(**profile_data(is_published=False))
        self.assertNotContains(self.client.get("/"), profile.full_name)
        profile.is_published = True
        profile.save()
        self.assertContains(self.client.get("/"), profile.full_name)
        profile.headline = "Capacitación ajustada a tu equipo"
        profile.save()
        self.assertContains(self.client.get("/"), profile.headline)
        profile.is_published = False
        profile.save()
        self.assertNotContains(self.client.get("/"), profile.headline)

    def test_home_has_requested_section_navigation(self):
        Profile.objects.create(**profile_data())
        response = self.client.get("/")
        for anchor in (
            "inicio", "sobre-mi", "servicios", "cursos", "experiencia", "formacion",
            "credenciales", "tecnologias", "proyectos", "recursos", "publicaciones", "contacto",
        ):
            with self.subTest(anchor=anchor):
                self.assertContains(response, f'id="{anchor}"')

    def test_whatsapp_includes_international_digits_and_escaped_message(self):
        profile = Profile(**profile_data(whatsapp="+56 9 3069 8473"))
        self.assertTrue(profile.whatsapp_url.startswith("https://wa.me/56930698473?text="))
        self.assertNotIn(" ", profile.whatsapp_url)

    def test_no_public_resume_button_for_private_document(self):
        asset = FileAsset.objects.create(title="CV sin autorizar", file="assets/cv.pdf")
        Profile.objects.create(**profile_data(resume=asset))
        response = self.client.get("/")
        self.assertNotContains(response, "Descargar currículum")
        self.assertNotContains(response, str(asset.pk))

    def test_health_checks_the_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)


class UploadValidationTests(SimpleTestCase):
    def test_svg_executable_and_html_are_rejected_regardless_of_mime(self):
        for name in ("imagen.svg", "ejecutable.exe", "documento.html"):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_upload(SimpleUploadedFile(name, b"<script>alert(1)</script>", content_type="image/png"))

    def test_invalid_content_and_mismatched_image_extension_are_rejected(self):
        files = [
            SimpleUploadedFile("falso.png", b"not an image", content_type="image/png"),
            SimpleUploadedFile("falso.pdf", b"<html>not a pdf</html>", content_type="application/pdf"),
            png_upload("imagen.jpg"),
        ]
        for file in files:
            with self.subTest(name=file.name), self.assertRaises(ValidationError):
                validate_upload(file)

    @override_settings(MAX_UPLOAD_SIZE=1024)
    def test_large_upload_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload(SimpleUploadedFile("grande.pdf", b"%PDF-1.7\n" + b"0" * 1024))

    def test_valid_image_is_accepted_and_rewound(self):
        file = png_upload()
        validate_upload(file)
        self.assertEqual(file.tell(), 0)


class AssetAccessTests(TestCase):
    def setUp(self):
        # Un backend real aislado: no dejar archivos de pruebas en el repositorio.
        self.directory = TemporaryDirectory()
        self.field = FileAsset._meta.get_field("file")
        self.original_storage = self.field.storage
        self.field.storage = FileSystemStorage(location=self.directory.name)
        self.addCleanup(self.restore_storage)

    def restore_storage(self):
        self.field.storage = self.original_storage
        self.directory.cleanup()

    def create_pdf(self, **overrides):
        data = {
            "title": "Currículum público",
            "file": SimpleUploadedFile("original-privado.pdf", b"%PDF-1.4\n%%EOF\n", content_type="application/pdf"),
            "is_public": False,
            "public_copy_confirmed": False,
        }
        data.update(overrides)
        asset = FileAsset(**data)
        asset.full_clean()
        asset.save()
        return asset

    def test_private_file_has_no_public_link_and_direct_request_returns_404(self):
        asset = self.create_pdf()
        self.assertEqual(asset.public_url, "")
        self.assertEqual(self.client.get(reverse("core:asset", args=[asset.pk])).status_code, 404)
        self.assertNotIn("original-privado", asset.file.name)
        self.assertTrue(Path(asset.file.path).is_file())

    def test_pdf_requires_explicit_review_before_publication(self):
        asset = self.create_pdf()
        asset.is_public = True
        with self.assertRaises(ValidationError):
            asset.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FileAsset.objects.filter(pk=asset.pk).update(is_public=True)

    def test_authorized_pdf_download_and_revocation(self):
        asset = self.create_pdf(is_public=True, public_copy_confirmed=True)
        response = self.client.get(asset.public_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4\n%%EOF\n")
        asset.is_public = False
        asset.save()
        self.assertEqual(self.client.get(reverse("core:asset", args=[asset.pk])).status_code, 404)

    def test_replacing_public_file_revokes_authorization_until_explicit_review(self):
        for update_fields in (None, {"file"}):
            with self.subTest(update_fields=update_fields):
                asset = self.create_pdf(is_public=True, public_copy_confirmed=True)
                url = asset.public_url
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                response.close()
                replacement = b"%PDF-1.4\n% Nueva version pendiente de revision\n%%EOF\n"
                asset.file = SimpleUploadedFile("nueva-version.pdf", replacement, content_type="application/pdf")
                asset.save(update_fields=update_fields)
                asset.refresh_from_db()
                self.assertFalse(asset.is_public)
                self.assertFalse(asset.public_copy_confirmed)
                self.assertEqual(asset.public_url, "")
                self.assertEqual(self.client.get(url).status_code, 404)
                asset.is_public = True
                asset.public_copy_confirmed = True
                asset.save()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b"".join(response.streaming_content), replacement)

    def test_authorized_image_is_inline_and_accessible(self):
        asset = FileAsset(
            title="Imagen autorizada", file=png_upload(), alt_text="Retrato profesional",
            is_public=True, public_copy_confirmed=True,
        )
        asset.full_clean()
        asset.save()
        response = self.client.get(asset.public_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("inline", response["Content-Disposition"])
        self.assertTrue(b"".join(response.streaming_content).startswith(b"\x89PNG"))

    def test_public_image_requires_alt_text(self):
        asset = FileAsset(title="Fotografía", file=png_upload(), is_public=True, public_copy_confirmed=True)
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_saved_photo_is_resized_oriented_and_stripped_of_private_metadata(self):
        source = BytesIO()
        exif = Image.Exif()
        exif[0x0112] = 6  # Rotación de cámara que debe aplicarse a los píxeles.
        exif[0x013B] = "Metadato privado de prueba"
        Image.new("RGB", (3200, 1600), color="#2563eb").save(source, format="JPEG", exif=exif)
        asset = FileAsset.objects.create(
            title="Retrato optimizado", file=SimpleUploadedFile("retrato.jpg", source.getvalue(), content_type="image/jpeg"),
        )
        with asset.file.open("rb") as file, Image.open(file) as saved:
            self.assertEqual(saved.size, (800, 1600))
            self.assertEqual(dict(saved.getexif()), {})
            self.assertNotIn("exif", saved.info)

    def test_direct_save_cannot_bypass_new_upload_validation(self):
        for filename, content in (("falsa.png", b"not an image"), ("activa.svg", b"<svg><script>alert(1)</script></svg>")):
            with self.subTest(filename=filename), self.assertRaises(ValidationError):
                FileAsset.objects.create(title="Carga inválida", file=SimpleUploadedFile(filename, content))
        self.assertEqual(FileAsset.objects.count(), 0)
        self.assertEqual(list(Path(self.directory.name).rglob("*")), [])

    def test_resume_rejects_image_and_photo_rejects_pdf(self):
        pdf = self.create_pdf()
        profile = Profile(**profile_data(photo=pdf))
        with self.assertRaises(ValidationError):
            profile.full_clean()
        image = FileAsset.objects.create(title="Imagen", file=png_upload())
        profile = Profile(**profile_data(resume=image))
        with self.assertRaises(ValidationError):
            profile.full_clean()


class RichTextTests(SimpleTestCase):
    def test_markdown_is_rendered_but_scripts_and_javascript_links_are_not_executable(self):
        from core.templatetags.content_tags import richtext

        output = str(richtext('**Conocimiento aplicado** <script>alert(1)</script> [clic](javascript:alert(1))'))
        self.assertIn("<strong>Conocimiento aplicado</strong>", output)
        self.assertNotIn("<script", output)
        self.assertNotIn('href="javascript:', output)


class InitialDataTests(TestCase):
    def test_import_is_repeatable_and_preserves_editor_changes(self):
        from training.models import TrainingCategory, TrainingService

        call_command("seed_initial_data", stdout=StringIO())
        profile = Profile.objects.get()
        self.assertEqual(profile.full_name, "Gastón Nicolás Salgado Jara")
        self.assertIsNone(profile.photo_id)
        self.assertIsNone(profile.resume_id)
        self.assertEqual(TrainingService.objects.count(), 10)
        self.assertEqual(TrainingCategory.objects.count(), 10)
        profile.headline = "Presentación editada por el propietario"
        profile.save()
        service = TrainingService.objects.first()
        service.summary = "Descripción revisada manualmente"
        service.save()
        call_command("seed_initial_data", stdout=StringIO())
        profile.refresh_from_db()
        service.refresh_from_db()
        self.assertEqual(profile.headline, "Presentación editada por el propietario")
        self.assertEqual(service.summary, "Descripción revisada manualmente")
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(SiteConfiguration.objects.count(), 1)
        self.assertEqual(TrainingService.objects.count(), 10)


class AdminAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("editor", "editor@example.test", "Testing-only-strong-password-897!")

    def test_admin_requires_authentication(self):
        response = self.client.get("/admin/")
        self.assertRedirects(response, "/admin/login/?next=/admin/")

    def test_anonymous_admin_submission_requires_csrf(self):
        from django.test import Client

        response = Client(enforce_csrf_checks=True).post("/admin/login/", {"username": "editor", "password": "Testing-only-strong-password-897!"})
        self.assertEqual(response.status_code, 403)

    def test_admin_edit_changes_public_profile_and_singletons_cannot_be_duplicated(self):
        profile = Profile.objects.create(**profile_data())
        SiteConfiguration.objects.create(seo_title="Perfil", seo_description="Descripción")
        self.client.force_login(self.user)
        url = reverse("admin:core_profile_change", args=[profile.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        data = profile_data(headline="Capacitación tecnológica para organizaciones")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertEqual(profile.headline, data["headline"])
        self.assertContains(self.client.get("/"), data["headline"])
        for model in ("profile", "siteconfiguration"):
            with self.subTest(model=model):
                self.assertEqual(self.client.get(reverse(f"admin:core_{model}_add")).status_code, 403)
                self.assertEqual(self.client.get(reverse(f"admin:core_{model}_delete", args=[1])).status_code, 403)

    def test_view_only_staff_cannot_publish_or_unpublish_through_forged_actions(self):
        from training.models import TrainingCategory, TrainingService
        from core.models import Technology

        viewer = get_user_model().objects.create_user("lector", is_staff=True)
        category = TrainingCategory.objects.create(name="Área de prueba", slug="area-prueba")
        service = TrainingService.objects.create(name="Servicio de prueba", slug="servicio-prueba", category=category, summary="Descripción")
        technology = Technology.objects.create(name="Tecnología de prueba", group=Technology.Group.TOOL)
        objects = (technology, category, service)
        for obj in objects:
            opts = obj._meta
            viewer.user_permissions.add(Permission.objects.get(content_type__app_label=opts.app_label, codename=f"view_{opts.model_name}"))
        self.client.force_login(viewer)
        for obj in objects:
            opts = obj._meta
            url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200)
            self.assertNotContains(page, '<option value="publish">')
            self.assertNotContains(page, '<option value="unpublish">')
            for action, original_state in (("publish", False), ("unpublish", True)):
                with self.subTest(model=opts.label, action=action):
                    obj.is_published = original_state
                    obj.save()
                    response = self.client.post(url, {"action": action, "_selected_action": str(obj.pk), "index": "0", "select_across": "0"})
                    self.assertIn(response.status_code, (200, 302, 403))
                    obj.refresh_from_db()
                    self.assertEqual(obj.is_published, original_state)
