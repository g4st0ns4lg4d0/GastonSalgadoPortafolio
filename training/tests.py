"""El catálogo de servicios no representa relatorías efectivamente impartidas."""
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from core.models import Technology
from .models import TrainingCategory, TrainingService


class ServicePublicationTests(TestCase):
    def setUp(self):
        self.category = TrainingCategory.objects.create(name="Área visible", slug="area-visible", is_published=True)
        self.service = TrainingService.objects.create(
            name="Servicio visible de capacitación", slug="servicio-visible",
            category=self.category, summary="Aprendizaje aplicado al trabajo.", is_published=True,
        )

    def test_only_published_services_in_published_categories_are_displayed(self):
        TrainingService.objects.create(
            name="Servicio privado de prueba", slug="servicio-privado", category=self.category,
            summary="Borrador", is_published=False,
        )
        hidden_category = TrainingCategory.objects.create(name="Área oculta", slug="area-oculta", is_published=False)
        TrainingService.objects.create(
            name="Servicio de categoría oculta", slug="servicio-area-oculta", category=hidden_category,
            summary="No publicar", is_published=True,
        )
        response = self.client.get("/")
        self.assertContains(response, self.service.name)
        self.assertNotContains(response, "Servicio privado de prueba")
        self.assertNotContains(response, "Servicio de categoría oculta")

    def test_hiding_a_category_also_hides_its_services(self):
        self.assertContains(self.client.get("/"), self.service.name)
        self.category.is_published = False
        self.category.save()
        self.assertNotContains(self.client.get("/"), self.service.name)

    def test_related_hidden_technology_is_not_published(self):
        visible = Technology.objects.create(name="Herramienta pública única", group=Technology.Group.TOOL, is_published=True)
        hidden = Technology.objects.create(name="Herramienta privada única", group=Technology.Group.TOOL, is_published=False)
        self.service.technologies.add(visible, hidden)
        response = self.client.get("/")
        self.assertContains(response, visible.name)
        self.assertNotContains(response, hidden.name)

    def test_manual_order_controls_display_order(self):
        self.service.position = 5
        self.service.save()
        TrainingService.objects.create(
            name="Servicio con prioridad editorial", slug="servicio-prioritario", category=self.category,
            summary="Primero en el catálogo.", position=1, is_published=True,
        )
        html = self.client.get("/").content.decode()
        self.assertLess(html.index("Servicio con prioridad editorial"), html.index(self.service.name))

    def test_referenced_category_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()
