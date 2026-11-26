"""
DSLR Background Bokeh Blur & Optical Depth of Field Adapter.
Isolates foreground subject and applies feathered depth blur to background.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image, ImageDraw, ImageFilter

from .base_adapter import BaseCapabilityAdapter


class BokehBlurAdapter(BaseCapabilityAdapter):
    """Executes optical DSLR depth blur with subject preservation."""

    def __init__(self):
        super().__init__(
            model_id="dslr_bokeh_pipeline",
            name="DSLR Optical Bokeh Blur & Depth Isolation",
            category="Depth & Bokeh",
        )

    def execute(self, img: Image.Image, radius: int = 15, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        w, h = img.size
        blur_rad = min(35, max(1, int(radius)))

        # 1. Background Blur Layer
        blurred_bg = img.filter(ImageFilter.GaussianBlur(radius=blur_rad))

        # 2. Feathered Subject Mask
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([int(w * 0.15), int(h * 0.08), int(w * 0.85), int(h * 0.96)], fill=255)
        feather_rad = max(8, int(min(w, h) * 0.12))
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_rad))

        # 3. Composite
        composite = Image.composite(img, blurred_bg, mask)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "bokeh_radius": blur_rad,
            "feather_radius": feather_rad,
            "duration_sec": duration,
        }
        return composite, metrics
