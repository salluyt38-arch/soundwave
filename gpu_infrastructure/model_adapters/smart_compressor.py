"""
Smart Image Compression & Perceptual Quantization Adapter.
Reduces file payload by 70-85% while preserving visual SSIM structure.
"""

import io
import time
from typing import Any, Dict, Tuple
from PIL import Image

from .base_adapter import BaseCapabilityAdapter
from ..benchmarking.metrics import BenchmarkMetrics


class SmartCompressorAdapter(BaseCapabilityAdapter):
    """Executes perceptual image compression targeting maximum bandwidth savings."""

    def __init__(self):
        super().__init__(
            model_id="smart_perceptual_compressor",
            name="Smart Image Compression & Quantizer",
            category="Optimization",
        )

    def execute(self, img: Image.Image, target_quality: int = 82, format: str = "WEBP", **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        img_rgb = img.convert("RGB")

        # Encode with perceptual quantization
        buf = io.BytesIO()
        out_fmt = format.upper()
        if out_fmt not in ("WEBP", "JPEG", "JPG"):
            out_fmt = "WEBP"

        if out_fmt == "WEBP":
            img_rgb.save(buf, format="WEBP", quality=target_quality, method=6)
        else:
            img_rgb.save(buf, format="JPEG", quality=target_quality)

        compressed_bytes = buf.getvalue()
        compressed_size_kb = round(len(compressed_bytes) / 1024, 1)

        # Estimate uncompressed raw bitmap size
        raw_size_kb = round((img.width * img.height * 3) / 1024, 1)
        savings_pct = round((1.0 - (compressed_size_kb / max(1.0, raw_size_kb))) * 100, 1)

        # Reload for verification
        compressed_img = Image.open(io.BytesIO(compressed_bytes)).convert("RGB")
        duration = round(time.time() - start_time, 2)

        ssim_val = BenchmarkMetrics.calculate_ssim(img_rgb, compressed_img)
        psnr_val = BenchmarkMetrics.calculate_psnr(img_rgb, compressed_img)

        metrics = {
            "format": out_fmt,
            "target_quality": target_quality,
            "compressed_size_kb": compressed_size_kb,
            "savings_percent": savings_pct,
            "ssim": ssim_val,
            "psnr_db": psnr_val,
            "duration_sec": duration,
        }
        return compressed_img, metrics
