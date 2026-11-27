"""
Professional Men's, Women's, and Universal AI Portrait Studio Engine.
Adheres strictly to zero automated gender classification.
Profiles are optional aesthetic styles chosen by the user.
Preserves authentic facial identity, skin micro-pores, facial hair, and eyelashes.
"""

from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from ..beauty.face_analyzer import FaceAnalyzer, FaceAnalysisResult, FaceGeometry
from ..beauty.gpupixel_engine import GPUPixelEngine

logger = logging.getLogger("gpu_infrastructure.portrait_studio.portrait_profiles")


class PortraitProfile(str, Enum):
    """The 3 Selectable Portrait Studio Profiles."""
    MEN = "men"
    WOMEN = "women"
    UNIVERSAL = "universal"


class PortraitStudioEngine:
    """
    Dedicated Men's & Women's Portrait Studio Processor.
    Implements targeted feature-preserving pipelines tailored to aesthetic preferences:
      - Men: Beard/stubble clarity, jawline definition, hair texture, clothing fabric recovery.
      - Women: Eyelash & iris clarity, eyebrow precision, luminous skin tone, lip vermilion pop.
      - Universal: Identity-neutral preservation, dynamic range recovery, authentic skin pores.
    """

    def __init__(self):
        self.analyzer = FaceAnalyzer()
        self.gpupixel = GPUPixelEngine()

    def process_portrait(
        self,
        img: Image.Image,
        profile: PortraitProfile = PortraitProfile.UNIVERSAL,
        skin_texture_fidelity: float = 85.0,  # 0 to 100 (high = preserve 100% pores)
        feature_clarity: float = 75.0,        # 0 to 100 (eyes, eyebrows, beard, hair)
        subtle_radiance: float = 20.0,        # 0 to 100
        clothing_recovery: bool = True,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Executes profile-specific portrait enhancement.
        Strictly preserves original identity and rejects artificial plastic smoothing.
        """
        analysis = self.analyzer.analyze(img)
        rgb_arr = np.array(img.convert("RGB"), dtype=np.float32)
        h, w = rgb_arr.shape[:2]

        fidelity_factor = max(0.2, min(1.0, float(skin_texture_fidelity) / 100.0))
        clarity_factor = max(0.1, min(1.0, float(feature_clarity) / 100.0))
        radiance_factor = max(0.0, min(1.0, float(subtle_radiance) / 100.0))

        # Skin and preservation masks from FaceAnalyzer
        skin_mask_f = (analysis.skin_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
        pres_mask_f = (analysis.feature_preservation_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

        # Multi-band frequency separation
        try:
            from scipy import ndimage
            base_band = ndimage.gaussian_filter(rgb_arr, sigma=(3.0, 3.0, 0))
        except ImportError:
            pil_blur = img.filter(ImageFilter.GaussianBlur(radius=3.0))
            base_band = np.array(pil_blur, dtype=np.float32)

        high_freq = rgb_arr - base_band
        processed = rgb_arr.copy()

        # =====================================================================
        # 1. PROFILE: MEN'S PORTRAIT STUDIO
        # =====================================================================
        if profile == PortraitProfile.MEN:
            # A. Beard & Moustache Detail Preservation (High micro-contrast on facial hair)
            beard_boost = high_freq * (1.0 + 0.65 * clarity_factor)
            processed = np.where(pres_mask_f > 0.3, base_band + beard_boost, processed)

            # B. Hair Strand & Clothing Texture Recovery
            if clothing_recovery:
                # Non-skin, non-face background and clothing enhancement
                clothing_mask = 1.0 - np.clip(skin_mask_f + pres_mask_f, 0.0, 1.0)
                clothing_texture = high_freq * (1.0 + 0.50 * clarity_factor)
                processed = processed + clothing_texture * clothing_mask * 0.40

            # C. Natural Skin Texture (Retains 85-95% natural pores; zero plastic blur)
            smooth_amount = (1.0 - fidelity_factor) * 0.35
            skin_smooth = base_band * smooth_amount + rgb_arr * (1.0 - smooth_amount)
            processed = processed * (1.0 - skin_mask_f) + skin_smooth * skin_mask_f

            # D. Matte Finish (Reduces harsh shine on forehead/nose)
            lum = (0.299 * processed[:, :, 0] + 0.587 * processed[:, :, 1] + 0.114 * processed[:, :, 2])
            high_spec = np.clip((lum - 215.0) / 40.0, 0.0, 1.0)[:, :, np.newaxis] * skin_mask_f
            processed -= high_spec * 14.0

        # =====================================================================
        # 2. PROFILE: WOMEN'S PORTRAIT STUDIO
        # =====================================================================
        elif profile == PortraitProfile.WOMEN:
            # A. Eyelashes, Eyebrows & Iris Catchlights Sharpness
            eye_boost = high_freq * (1.0 + 0.75 * clarity_factor)
            processed = np.where(pres_mask_f > 0.3, base_band + eye_boost, processed)

            # B. Natural Complexion & Subtle Radiance Lift
            if radiance_factor > 0.0:
                luma = (0.299 * processed[:, :, 0] + 0.587 * processed[:, :, 1] + 0.114 * processed[:, :, 2]) / 255.0
                lift = np.sin(luma * np.pi) * (radiance_factor * 18.0)
                processed += lift[:, :, np.newaxis] * skin_mask_f

            # C. Natural Skin Smoothing while keeping 75-85% micro-pores
            smooth_amount = (1.0 - fidelity_factor) * 0.45
            skin_smooth = base_band * smooth_amount + rgb_arr * (1.0 - smooth_amount)
            processed = processed * (1.0 - skin_mask_f) + skin_smooth * skin_mask_f

            # D. Lip Vermilion & Natural Makeup Definition
            # Subtle saturation lift on lips
            for geo in analysis.faces:
                if geo.mouth_box:
                    mx, my, mw, mh = geo.mouth_box
                    y1, y2 = max(0, my), min(h, my + mh)
                    x1, x2 = max(0, mx), min(w, mx + mw)
                    if y2 > y1 and x2 > x1:
                        mouth_patch = processed[y1:y2, x1:x2]
                        # Boost red chrominance gently
                        mouth_patch[:, :, 0] = np.clip(mouth_patch[:, :, 0] * 1.05, 0.0, 255.0)

        # =====================================================================
        # 3. PROFILE: UNIVERSAL NATURAL PORTRAIT
        # =====================================================================
        else:
            # A. True Identity Preservation: Pure texture restoration
            eye_hair_boost = high_freq * (1.0 + 0.45 * clarity_factor)
            processed = np.where(pres_mask_f > 0.3, base_band + eye_hair_boost, processed)

            # B. Faithful Skin Pores (90%+ retention)
            smooth_amount = (1.0 - fidelity_factor) * 0.25
            skin_smooth = base_band * smooth_amount + rgb_arr * (1.0 - smooth_amount)
            processed = processed * (1.0 - skin_mask_f) + skin_smooth * skin_mask_f

        out_arr = np.clip(processed, 0.0, 255.0).astype(np.uint8)
        out_img = Image.fromarray(out_arr)

        metrics = {
            "profile": profile.value,
            "skin_texture_fidelity_pct": round(fidelity_factor * 100.0, 1),
            "feature_clarity_pct": round(clarity_factor * 100.0, 1),
            "faces_analyzed": len(analysis.faces),
            "beard_regions_detected": any(f.has_facial_hair for f in analysis.faces),
            "lighting_condition": analysis.lighting.condition,
        }

        return out_img, metrics
