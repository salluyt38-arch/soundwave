"""
JPEG Artifact Removal & Block Boundary Deblocking Adapter.
Removes 8x8 DCT grid compression blocks, moshing artifacts, and high-frequency ringing.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image

try:
    import cv2
    import numpy as np
    CV_OK = True
except ImportError:
    CV_OK = False

from .base_adapter import BaseCapabilityAdapter


class JpegDeblockAdapter(BaseCapabilityAdapter):
    """Executes JPEG de-ringing and 8x8 grid boundary smoothing."""

    def __init__(self):
        super().__init__(
            model_id="jpeg_deblock_engine",
            name="JPEG Artifact & Compression Ringing Deblocker",
            category="Restoration",
        )

    def execute(self, img: Image.Image, strength: float = 1.0, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        w, h = img.size
        img_rgb = img.convert("RGB")

        if not CV_OK:
            from PIL import ImageFilter
            deblocked = img_rgb.filter(ImageFilter.SMOOTH)
            duration = round(time.time() - start_time, 2)
            return deblocked, {"method": "pil_smooth_fallback", "duration_sec": duration}

        arr = np.array(img_rgb)

        # 1. Edge-preserving surface blur to smooth 8x8 DCT grid discontinuities
        d = max(3, int(5 * strength))
        sigma_color = int(25 * strength)
        sigma_space = int(15 * strength)
        deblocked = cv2.bilateralFilter(arr, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

        # 2. Subtle unsharp mask to restore genuine underlying fine textures
        gaussian = cv2.GaussianBlur(deblocked, (0, 0), 1.5)
        sharpened = cv2.addWeighted(deblocked, 1.25, gaussian, -0.25, 0)

        res_img = Image.fromarray(sharpened)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "strength": strength,
            "method": "bilateral_dct_grid_deblocking",
            "duration_sec": duration,
        }
        return res_img, metrics
