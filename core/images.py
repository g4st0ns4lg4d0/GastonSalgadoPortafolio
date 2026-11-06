from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def optimize_image(upload):
    """Normaliza orientación/tamaño y elimina EXIF, GPS y otros metadatos."""
    suffix = Path(upload.name).suffix.lower()
    image = ImageOps.exif_transpose(Image.open(upload))
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
    image = image.convert("RGBA" if has_alpha and suffix != ".jpg" and suffix != ".jpeg" else "RGB")
    # Copiar solo los píxeles impide conservar accidentalmente metadatos.
    clean = Image.new(image.mode, image.size)
    clean.paste(image)
    output = BytesIO()
    format_name = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[suffix]
    options = {"optimize": True} if format_name == "PNG" else {"quality": 85}
    clean.save(output, format=format_name, **options)
    return ContentFile(output.getvalue(), name=upload.name)
