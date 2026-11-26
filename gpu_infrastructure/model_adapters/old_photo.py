"""
Archival Old Photo Restoration & Scratch Healer Adapter.
Heals cracks, scratches, tears, and recovers faded historical contrast.
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


class OldPhotoRestorationAdapter(BaseCapabilityAdapter):
    """Executes archival restoration for vintage and damaged photographs."""

    def __init__(self):
        super().__init__(
            model_id="old_photo_healer_v2",
            name="Archival Old Photo Restoration & Scratch Healer",
            category="Restoration",
        )

    def execute(self, img: Image.Image, remove_scratches: bool = True, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        w, h = img.size
        img_rgb = img.convert("RGB")

        if not CV_OK:
            from PIL import ImageEnhance, ImageFilter
            smooth = img_rgb.filter(ImageFilter.MedianFilter(size=3))
            contrast = ImageEnhance.Contrast(smooth).enhance(1.2)
            duration = round(time.time() - start_time, 2)
            return contrast, {"method": "pil_median_fallback", "duration_sec": duration}

        arr = np.array(img_rgb)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        if remove_scratches:
            # Detect scratches via morphological black-hat / top-hat filter
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            top_hat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
            _, scratch_mask = cv2.threshold(top_hat, 28, 255, cv2.THRESH_BINARY)
            # Inpaint detected scratch regions
            arr = cv2.inpaint(arr, scratch_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        # Bilateral edge-preserving defect smoothing
        smoothed = cv2.bilateralFilter(arr, d=5, sigmaColor=35, sigmaSpace=25)

        # Contrast recovery via CLAHE
        lab = cv2.cvtColor(smoothed, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        restored_lab = cv2.merge((cl, a, b))
        restored_rgb = cv2.cvtColor(restored_lab, cv2.COLOR_LAB2RGB)

        res_img = Image.fromarray(restored_rgb)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "remove_scratches": remove_scratches,
            "method": "telea_inpaint_clahe_restoration",
            "duration_sec": duration,
        }
        return res_img, metrics
