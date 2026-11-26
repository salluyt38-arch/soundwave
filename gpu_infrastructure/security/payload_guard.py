"""
Security and Payload Validation Guard for AI Image Processing.
Guarantees input safety, MIME verification, dimension clamping, and memory exhaustion protection.
"""

import io
import logging
from typing import Tuple
from PIL import Image

logger = logging.getLogger("gpu_infrastructure.security")

# Permitted MIME types and formats
ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "TIFF", "BMP"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max payload
MIN_DIMENSION = 16
MAX_DIMENSION = 8192


class PayloadGuard:
    """Security boundaries validator for all incoming image payloads."""

    @staticmethod
    def validate_image_bytes(raw_bytes: bytes) -> Tuple[bool, str, Image.Image]:
        """
        Validates raw bytes at trust boundary.
        Returns (is_valid, error_message, PIL_Image).
        """
        if not raw_bytes or len(raw_bytes) < 16:
            return False, "Payload is empty or too small to be a valid image.", None

        if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
            return False, f"Payload size exceeds safety limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.", None

        try:
            # Verify image header without decoding entire stream first
            stream = io.BytesIO(raw_bytes)
            img = Image.open(stream)
            img_format = (img.format or "").upper()

            if img_format not in ALLOWED_FORMATS:
                return False, f"Unsupported image format: {img_format}. Allowed: {', '.join(ALLOWED_FORMATS)}", None

            w, h = img.size
            if w < MIN_DIMENSION or h < MIN_DIMENSION:
                return False, f"Image dimensions too small ({w}x{h}). Minimum is {MIN_DIMENSION}x{MIN_DIMENSION}.", None

            if w > MAX_DIMENSION or h > MAX_DIMENSION:
                return False, f"Image dimensions exceed maximum safe limit ({w}x{h}). Max is {MAX_DIMENSION}x{MAX_DIMENSION}.", None

            # Fully load pixel buffer to catch truncated or corrupted files
            img.load()
            clean_rgb = img.convert("RGB")
            return True, "", clean_rgb

        except Exception as e:
            logger.warning(f"Malicious or corrupted payload rejected: {str(e)}")
            return False, f"Invalid image payload: {str(e)}", None
