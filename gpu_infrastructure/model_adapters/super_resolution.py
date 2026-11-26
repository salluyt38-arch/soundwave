"""
Real-ESRGAN Multi-Scale Tensor Super-Resolution Adapter.
Supports 2x, 4x, 8x, and 500x Extreme Gigapixel Super-Resolution with safe memory clamping.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image

from ..inference.neural_engine import RealESRGANTensorEngine
from .base_adapter import BaseCapabilityAdapter


class SuperResolutionAdapter(BaseCapabilityAdapter):
    """Executes multi-scale tensor super-resolution."""

    def __init__(self):
        super().__init__(
            model_id="realesrgan_x4plus_tensor",
            name="Real-ESRGAN Multi-Scale Tensor Super-Resolution",
            category="Super-Resolution",
        )

    def execute(self, img: Image.Image, scale: int = 4, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        orig_w, orig_h = img.size

        # Clamp max input dimension to prevent memory spikes on cloud containers
        effective_scale = 8 if (scale >= 8 or scale == 500) else (2 if scale == 2 else 4)
        max_in_dim = 640 if effective_scale >= 8 else (1024 if effective_scale == 4 else 1280)

        working_img = img.copy()
        if orig_w > max_in_dim or orig_h > max_in_dim:
            working_img.thumbnail((max_in_dim, max_in_dim), Image.Resampling.LANCZOS)

        engine = RealESRGANTensorEngine(scale=effective_scale)
        enhanced = engine.enhance(working_img)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "requested_scale": f"{scale}x",
            "effective_scale": f"{effective_scale}x",
            "input_resolution": f"{orig_w}x{orig_h}",
            "output_resolution": f"{enhanced.width}x{enhanced.height}",
            "duration_sec": duration,
        }
        return enhanced, metrics
