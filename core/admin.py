from django import forms
from django.contrib import admin, messages
from django.db import models
from django.utils.html import format_html

from .models import FileAsset, Organization, Profile, SiteConfiguration, Technology
from .widgets import MarkdownWidget

admin.site.site_header = "Gastón Salgado · Administración"
admin.site.site_title = "Administración profesional"
admin.site.index_title = "Gestiona tu plataforma"


class ContentAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {models.TextField: {"widget": MarkdownWidget}}
    save_on_top = True


class SingletonAdmin(ContentAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Profile)
class ProfileAdmin(SingletonAdmin):
    list_display = ("full_name", "professional_title", "is_published", "updated_at")
    autocomplete_fields = ("photo", "resume")
    fieldsets = (
        ("Presentación", {"fields": ("full_name", "professional_title", "headline", "introduction", "is_published")}),
        ("Sobre mí", {"fields": ("biography_technology", "biography_teaching", "teaching_methodology")}),
        ("Ubicación y contacto", {"fields": ("location", "coverage", "email", "whatsapp", "linkedin_url")}),
        ("Fotografía y currículum", {"description": "Solo se mostrarán archivos con acceso público autorizado. No publiques documentos con información sensible.", "fields": ("photo", "resume")}),
        ("Registro", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    def view_on_site(self, obj):
        return "/"


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(SingletonAdmin):
    list_display = ("site_name", "seo_title", "updated_at")


@admin.register(FileAsset)
class FileAssetAdmin(ContentAdmin):
    list_display = ("title", "is_public", "public_copy_confirmed", "created_at", "public_preview")
    list_filter = ("is_public", "public_copy_confirmed")
    search_fields = ("title", "alt_text")
    formfield_overrides = {
        **ContentAdmin.formfield_overrides,
        models.FileField: {"widget": forms.FileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png,.webp"})},
    }
    readonly_fields = (*ContentAdmin.readonly_fields, "stored_file_status", "public_preview")
    fields = ("title", "stored_file_status", "file", "alt_text", "license", "public_copy_confirmed", "is_public", "public_preview", "created_at", "updated_at")

    @admin.display(description="Archivo guardado")
    def stored_file_status(self, obj):
        return "Hay un archivo guardado. Reemplazarlo revoca su publicación y exige una nueva autorización." if obj and obj.file else "Sin archivo"

    def save_model(self, request, obj, form, change):
        replaced = change and "file" in form.changed_data
        super().save_model(request, obj, form, change)
        if replaced:
            self.message_user(request, "Nueva versión guardada como privada. Revísala y vuelve a autorizar su publicación si corresponde.", level=messages.WARNING)

    @admin.display(description="Vista pública")
    def public_preview(self, obj):
        if obj and obj.public_url:
            return format_html('<a href="{}" target="_blank" rel="noopener">Consultar versión pública</a>', obj.public_url)
        return "Privado"


@admin.register(Organization)
class OrganizationAdmin(ContentAdmin):
    list_display = ("name", "website")
    search_fields = ("name",)
    autocomplete_fields = ("logo",)


class PublicationAdmin(ContentAdmin):
    list_filter = ("is_published",)
    actions = ("publish", "unpublish")

    @admin.action(description="Publicar los registros seleccionados", permissions=["change"])
    def publish(self, request, queryset):
        for obj in queryset:
            obj.is_published = True
            obj.save(update_fields=["is_published", "updated_at"])

    @admin.action(description="Ocultar los registros seleccionados", permissions=["change"])
    def unpublish(self, request, queryset):
        for obj in queryset:
            obj.is_published = False
            obj.save(update_fields=["is_published", "updated_at"])


@admin.register(Technology)
class TechnologyAdmin(PublicationAdmin):
    list_display = ("name", "group", "position", "is_published")
    list_editable = ("position", "is_published")
    list_filter = ("group", "is_published")
    search_fields = ("name",)
