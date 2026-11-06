from django.contrib import admin
from core.admin import PublicationAdmin
from .models import TrainingCategory, TrainingService


@admin.register(TrainingCategory)
class TrainingCategoryAdmin(PublicationAdmin):
    list_display = ("name", "position", "is_published")
    list_editable = ("position", "is_published")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TrainingService)
class TrainingServiceAdmin(PublicationAdmin):
    list_display = ("name", "category", "position", "is_published")
    list_editable = ("position", "is_published")
    list_filter = ("category", "is_published")
    search_fields = ("name", "summary", "description", "technologies__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "technologies", "image")
    fieldsets = (
        ("Servicio ofrecido", {"description": "Este catálogo describe áreas de capacitación. No acredita cursos efectivamente impartidos.", "fields": ("name", "slug", "category", "summary", "description")}),
        ("Presentación", {"fields": ("icon", "image", "technologies", "position", "is_published")}),
        ("Registro", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    def view_on_site(self, obj):
        return "/#servicios"
