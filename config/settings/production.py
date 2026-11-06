from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or "development-only" in SECRET_KEY:
    raise ImproperlyConfigured("Producción requiere DJANGO_SECRET_KEY aleatoria de al menos 50 caracteres.")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Configura DJANGO_ALLOWED_HOSTS con los dominios concretos.")
if urlsplit(SITE_URL).scheme != "https" or not urlsplit(SITE_URL).netloc:
    raise ImproperlyConfigured("Producción requiere SITE_URL con https y dominio definitivo.")
DATABASES = {"default": env.db("DATABASE_URL")}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Usa PostgreSQL en producción mediante DATABASE_URL.")
DATABASES["default"]["CONN_MAX_AGE"] = 60
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[SITE_URL])
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Activar solo detrás de un proxy de confianza que REEMPLACE esta cabecera.
if env.bool("DJANGO_TRUST_PROXY", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": STATICFILES_STORAGE},
}
