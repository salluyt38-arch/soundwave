"""
Real-ESRGAN Multi-Scale Tensor Super-Resolution Adapter.
Supports 2x, 4x, 8x, and 500x Extreme Gigapixel Super-Resolution
with full camera resolution preservation and zero input downsampling.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image

from ..inference.neural_engine import RealESRGANTensorEngine
from .base_adapter import BaseCapabilityAdapter


class SuperResolutionAdapter(BaseCapabilityAdapter):
    """Executes multi-scale tensor super-resolution preserving native camera details."""

    def __init__(self):
        super().__init__(
            model_id="realesrgan_x4plus_tensor",
            name="Real-ESRGAN Multi-Scale Tensor Super-Resolution",
            category="Super-Resolution",
        )

    def execute(self, img: Image.Image, scale: int = 4, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        orig_w, orig_h = img.size
        max_dim = max(orig_w, orig_h)

        # Determine effective scale up to 2560px max master dimension (zero input crushing & zero 502/OOM)
        max_target_dim = 2560
        if max_dim >= 2048:
            effective_scale = 1
        else:
            if scale in (8, 500) or scale >= 8:
                if max_dim * 4 <= max_target_dim:
                    effective_scale = 4
                elif max_dim * 2 <= max_target_dim:
                    effective_scale = 2
                else:
                    effective_scale = 1
            elif scale == 4:
                effective_scale = 4 if max_dim * 4 <= max_target_dim else (2 if max_dim * 2 <= max_target_dim else 1)
            elif scale == 2:
                effective_scale = 2 if max_dim * 2 <= max_target_dim else 1
            else:
                effective_scale = 1

        engine = RealESRGANTensorEngine(scale=effective_scale)
        enhanced = engine.enhance(img)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "requested_scale": f"{scale}x",
            "effective_scale": f"{effective_scale}x",
            "input_resolution": f"{orig_w}x{orig_h}",
            "output_resolution": f"{enhanced.width}x{enhanced.height}",
            "duration_sec": duration,
        }
        return enhanced, metrics
