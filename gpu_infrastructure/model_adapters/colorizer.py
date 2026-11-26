"""
Deep Spectrum B&W Photo Colorizer Adapter.
Synthesizes natural organic colors for monochrome and sepia historical photographs.
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


class PhotoColorizerAdapter(BaseCapabilityAdapter):
    """Executes monochrome colorization using luminance mapping."""

    def __init__(self):
        super().__init__(
            model_id="ddcolor_chroma_mapper",
            name="Deep Spectrum B&W Photo Colorizer",
            category="Colorization",
        )

    def execute(self, img: Image.Image, saturation: float = 1.15, warmth: float = 1.05, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        img_rgb = img.convert("RGB")
        w, h = img.size

        if not CV_OK:
            from PIL import ImageEnhance
            colorized = ImageEnhance.Color(img_rgb).enhance(saturation)
            duration = round(time.time() - start_time, 2)
            return colorized, {"method": "pil_color_enhance_fallback", "duration_sec": duration}

        arr = np.array(img_rgb)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Synthesize chrominance channels (a and b in LAB space)
        # Mid-tone luminance (skin tones): warm reddish-yellow prior (a > 128, b > 128)
        # High-tone luminance (sky/background): subtle cool cyan/blue prior
        # Low-tone luminance (shadows/clothing): neutral dark navy
        l_norm = gray.astype(np.float32) / 255.0

        # Organic warm prior for skin/nature midtones (l ~ 0.35 to 0.75)
        skin_prior = np.exp(-((l_norm - 0.55) ** 2) / 0.08)
        a_channel = 128.0 + (18.0 * warmth * skin_prior) - (8.0 * (1.0 - skin_prior))
        b_channel = 128.0 + (22.0 * warmth * skin_prior) - (12.0 * (1.0 - skin_prior))

        a_channel = np.clip(a_channel * saturation, 0, 255).astype(np.uint8)
        b_channel = np.clip(b_channel * saturation, 0, 255).astype(np.uint8)

        lab = cv2.merge((gray, a_channel, b_channel))
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        res_img = Image.fromarray(rgb)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "saturation": saturation,
            "warmth": warmth,
            "method": "lab_luminance_prior_colorization",
            "duration_sec": duration,
        }
        return res_img, metrics
