from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage():
    # Callable serializable en migraciones y compatible con overrides de tests.
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
