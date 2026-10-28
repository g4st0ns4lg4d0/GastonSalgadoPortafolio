from django import forms


class MarkdownWidget(forms.Textarea):
    """Editor local y progresivo: sigue siendo usable sin JavaScript."""
    template_name = "core/widgets/markdown.html"

    class Media:
        css = {"all": ("css/admin-editor.css",)}
        js = ("js/admin-editor.js",)
