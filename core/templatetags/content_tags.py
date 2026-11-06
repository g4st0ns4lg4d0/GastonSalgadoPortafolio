import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def richtext(value):
    """Markdown acotado, nunca HTML arbitrario del administrador."""
    html = markdown.markdown(str(value or ""), extensions=["sane_lists"])
    safe = bleach.clean(html, tags={"p", "br", "strong", "em", "ul", "ol", "li", "blockquote", "code", "pre", "h3", "h4", "a"}, attributes={"a": ["href", "title"]}, protocols={"https", "http", "mailto"}, strip=True)
    return mark_safe(safe)  # noqa: S308 - sanitizado arriba
