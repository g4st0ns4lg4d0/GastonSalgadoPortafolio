from pathlib import Path

from django.conf import settings
from django.db import connection
from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from training.models import TrainingService
from .models import FileAsset, Profile, SiteConfiguration, Technology


@require_GET
def home(request):
    profile = Profile.objects.filter(is_published=True).select_related("photo", "resume").first()
    site_config = SiteConfiguration.objects.first()
    services = TrainingService.objects.filter(is_published=True, category__is_published=True).select_related("category", "image").prefetch_related(Prefetch("technologies", queryset=Technology.objects.filter(is_published=True)))
    # Catálogo de competencias se completa en la etapa 2. No se inventan registros.
    technology_groups = []
    for value, label in Technology.Group.choices:
        technologies = list(Technology.objects.filter(is_published=True, group=value))
        if technologies:
            technology_groups.append((label, technologies))
    return render(request, "core/home.html", {"profile": profile, "site_config": site_config, "services": services, "technology_groups": technology_groups, "canonical_url": settings.SITE_URL + "/"})


@require_GET
def asset(request, pk):
    record = get_object_or_404(FileAsset, pk=pk, is_public=True, public_copy_confirmed=True)
    suffix = Path(record.file.name).suffix.lower()
    content_types = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    if suffix not in content_types:
        raise Http404
    try:
        handle = record.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404 from None
    response = FileResponse(handle, as_attachment=suffix == ".pdf", filename=f"{slugify(record.title) or 'documento'}{suffix}", content_type=content_types[suffix])
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex, noarchive"
    return response


@require_GET
def health(request):
    # Respuesta mínima; no expone versiones, credenciales ni rutas.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


@require_GET
def robots(request):
    return HttpResponse("User-agent: *\nDisallow: /admin/\nDisallow: /archivos/\n", content_type="text/plain")
