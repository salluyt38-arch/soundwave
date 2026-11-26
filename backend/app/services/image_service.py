"""
APEX Image Service
EXIF orientation correction, format encoding, and Base64 stream translation.
"""

import base64
import io
from typing import Tuple
from PIL import Image, ImageOps
from ..config import MAX_INPUT_DIMENSION, MIN_INPUT_DIMENSION


class ImageService:
    """
    Standardizes image ingestion, EXIF correction, and output streaming.
    """

    @staticmethod
    def decode_image(payload: str) -> Image.Image:
        """
        Decodes base64 string or data URL into an orientation-corrected PIL Image.
        """
        raw_b64 = payload.strip()
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]

        try:
            img_bytes = base64.b64decode(raw_b64)
            img = Image.open(io.BytesIO(img_bytes))

            # Apply EXIF orientation (crucial for iPhone & Android portrait orientation)
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")

            w, h = img.size
            if w < MIN_INPUT_DIMENSION or h < MIN_INPUT_DIMENSION:
                raise ValueError(f"Image is too small ({w}x{h}). Minimum size is {MIN_INPUT_DIMENSION}px.")

            if w > MAX_INPUT_DIMENSION or h > MAX_INPUT_DIMENSION:
                img.thumbnail((MAX_INPUT_DIMENSION, MAX_INPUT_DIMENSION), Image.Resampling.LANCZOS)

            return img
        except Exception as e:
            raise ValueError(f"Failed to decode image payload: {str(e)}")

    @staticmethod
    def image_to_base64(img: Image.Image, format_name: str = "JPEG", quality: int = 95) -> str:
        """
        Encodes a PIL Image into a base64 data URL.
        """
        buf = io.BytesIO()
        fmt = format_name.upper()
        if fmt in ["JPG", "JPEG"]:
            img.save(buf, format="JPEG", quality=quality, optimize=True)
            mime = "image/jpeg"
        elif fmt == "PNG":
            img.save(buf, format="PNG", optimize=True)
            mime = "image/png"
        elif fmt == "WEBP":
            img.save(buf, format="WEBP", quality=quality)
            mime = "image/webp"
        else:
            img.save(buf, format="JPEG", quality=quality)
            mime = "image/jpeg"

        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:{mime};base64,{b64_str}"

    @staticmethod
    def image_to_bytes(img: Image.Image, format_name: str = "JPEG", quality: int = 95) -> bytes:
        """
        Encodes a PIL Image into raw bytes.
        """
        buf = io.BytesIO()
        fmt = format_name.upper()
        if fmt in ["JPG", "JPEG"]:
            img.save(buf, format="JPEG", quality=quality)
        elif fmt == "PNG":
            img.save(buf, format="PNG")
        elif fmt == "WEBP":
            img.save(buf, format="WEBP", quality=quality)
        else:
            img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
