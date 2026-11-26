"""
GFPGAN v1.4 Remini Face Beauty & Texture Polish Adapter.
Executes face detection, ocular catchlights, lip contour polish, and frequency separation.
"""

import time
from typing import Any, Dict, Tuple
from PIL import Image

from ..inference.neural_engine import GFPGANFacialRestorer
from .base_adapter import BaseCapabilityAdapter


class FaceRestorationAdapter(BaseCapabilityAdapter):
    """Executes Remini-grade face restoration with identity preservation."""

    def __init__(self):
        super().__init__(
            model_id="gfpgan_v14_remini",
            name="GFPGAN v1.4 Remini Face Beauty Engine",
            category="Face Restoration",
        )

    def execute(self, img: Image.Image, fidelity_weight: float = 0.85, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        restorer = GFPGANFacialRestorer(fidelity_weight=fidelity_weight)
        restored = restorer.restore_face(img)
        duration = round(time.time() - start_time, 2)

        metrics = {
            "fidelity_weight": fidelity_weight,
            "duration_sec": duration,
            "operation": "face_beauty_frequency_separation",
        }
        return restored, metrics
