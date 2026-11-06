from pathlib import Path
import warnings

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def validate_upload(value):
    """Formato y contenido; ni HTML/SVG ni documentos con macros."""
    suffix = Path(value.name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError("Solo se permiten PDF, JPG, PNG y WebP.")
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError("El archivo no puede superar 8 MB.")
    try:
        value.open("rb")
        if suffix == ".pdf":
            if value.read(5) != b"%PDF-":
                raise ValidationError("El archivo no contiene una cabecera PDF válida.")
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                image = Image.open(value)
                expected = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[suffix]
                if image.format != expected:
                    raise ValidationError("El contenido de la imagen no coincide con su extensión.")
                if image.width * image.height > 24_000_000:
                    raise ValidationError("La imagen supera 24 megapíxeles. Redúcela antes de cargarla.")
                image.verify()
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("No se pudo validar el archivo. Utiliza una imagen o PDF válido.") from exc
    finally:
        value.seek(0)
