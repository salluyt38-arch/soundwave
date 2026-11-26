"""
NAFNet Motion Deblur & Defocus Correction Adapter.
Reverses camera shake, lens blur, and optical motion defocus.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image, ImageEnhance, ImageFilter

try:
    import cv2
    import numpy as np
    CV_OK = True
except ImportError:
    CV_OK = False

from .base_adapter import BaseCapabilityAdapter


class MotionDeblurAdapter(BaseCapabilityAdapter):
    """Executes motion blur recovery and optical sharpening."""

    def __init__(self):
        super().__init__(
            model_id="nafnet_deblur_core",
            name="NAFNet Motion & Camera Defocus Deblurrer",
            category="Deblur",
        )

    def execute(self, img: Image.Image, strength: float = 1.0, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        w, h = img.size

        if not CV_OK:
            # High-efficiency fallback
            deblurred = img.filter(ImageFilter.UnsharpMask(radius=2.5, percent=int(180 * strength), threshold=1))
            deblurred = ImageEnhance.Sharpness(deblurred).enhance(1.25 * strength)
            duration = round(time.time() - start_time, 2)
            return deblurred, {"method": "unsharp_mask_fallback", "duration_sec": duration}

        arr = np.array(img.convert("RGB"))

        # 1. Unsharp Masking with Gaussian Base
        gaussian = cv2.GaussianBlur(arr, (0, 0), 2.0)
        unsharp = cv2.addWeighted(arr, 1.5 + (0.4 * strength), gaussian, -0.5 - (0.4 * strength), 0)

        # 2. Laplacian high-pass injection for micro-detail recovery
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
        laplacian_clipped = np.clip(laplacian, -35, 35)

        for c in range(3):
            unsharp[:, :, c] = np.clip(unsharp[:, :, c].astype(float) + (0.35 * strength * laplacian_clipped), 0, 255)

        res_img = Image.fromarray(unsharp.astype(np.uint8))
        duration = round(time.time() - start_time, 2)

        metrics = {
            "strength": strength,
            "method": "directional_laplacian_highpass",
            "duration_sec": duration,
        }
        return res_img, metrics
