"""
Professional Colour Science Engine.
Features 9 master colour science profiles calibrated for high-fidelity photography.
Disclaimer: These profiles are original algorithmic aesthetic implementations inspired
by legendary photographic aesthetics and are not official manufacturer color profiles
or optical equivalents.
"""

from enum import Enum
import logging
from typing import Any, Dict, Tuple
import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger("gpu_infrastructure.color_science.color_profiles")


class ColorProfile(str, Enum):
    """The 9 Professional Master Colour Science Profiles."""
    NATURAL_PRO = "natural_pro"
    ZEISS_NATURAL = "zeiss_natural"
    LEICA_CONTRAST = "leica_contrast"
    HASSELBLAD_COLOR = "hasselblad_color"
    CINEMATIC = "cinematic"
    STUDIO_PORTRAIT = "studio_portrait"
    WARM_PORTRAIT = "warm_portrait"
    COOL_PORTRAIT = "cool_portrait"
    NEUTRAL_EDITORIAL = "neutral_editorial"


class ProfessionalColorEngine:
    """
    Applies calibrated photometric 3D color matrices, S-curves, and tonal LUTs.
    Preserves natural human skin tonality while providing distinct artistic signatures.
    """

    def apply_profile(
        self,
        img: Image.Image,
        profile: ColorProfile = ColorProfile.NATURAL_PRO,
        intensity: float = 100.0,  # 0 to 100
        skin_protection: bool = True,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """Applies photographic color grading with controllable intensity."""
        alpha = max(0.0, min(1.0, float(intensity) / 100.0))
        if alpha == 0.0:
            return img.copy(), {"profile": profile.value, "intensity": 0, "applied": False}

        arr = np.array(img.convert("RGB"), dtype=np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

        # Segment skin locus in YCbCr to protect facial tones from aggressive color shifts
        cr = (r - luma * 255.0) * 0.713 + 128.0
        cb = (b - luma * 255.0) * 0.564 + 128.0
        skin_mask = ((cr >= 133.0) & (cr <= 175.0) & (cb >= 80.0) & (cb <= 130.0)).astype(np.float32)[:, :, np.newaxis]

        norm = arr / 255.0
        styled = norm.copy()

        if profile == ColorProfile.NATURAL_PRO:
            # 1. Natural Professional: True-to-life reference, subtle contrast calibration
            styled = np.power(styled, 1.04)
            # Gentle vibrance (increases low-saturation areas without blowing saturated colors)
            max_c = np.max(styled, axis=2, keepdims=True)
            min_c = np.min(styled, axis=2, keepdims=True)
            sat = max_c - min_c
            styled += (styled - luma[:, :, np.newaxis]) * (1.0 - sat) * 0.12

        elif profile == ColorProfile.ZEISS_NATURAL:
            # 2. ZEISS-inspired Natural: Micro-contrast clarity, crisp 3D pop, clean neutral blues
            # Micro-contrast S-curve
            styled = 0.5 + np.sin((styled - 0.5) * np.pi * 0.85) * 0.55
            # Cool shadow tone & clean specular highlights
            styled[:, :, 2] += (1.0 - luma) * 0.02
            styled[:, :, 0] += (luma - 0.5) * 0.02

        elif profile == ColorProfile.LEICA_CONTRAST:
            # 3. Leica-inspired Contrast: Deep velvety shadows, sharp highlight restraint
            # Deep toe roll-off in shadows
            shadow_zone = np.clip((0.35 - luma) / 0.35, 0.0, 1.0)[:, :, np.newaxis]
            styled -= shadow_zone * 0.08
            # Subtle desaturation towards classic documentary tone
            mean_channel = np.mean(styled, axis=2, keepdims=True)
            styled = styled * 0.88 + mean_channel * 0.12

        elif profile == ColorProfile.HASSELBLAD_COLOR:
            # 4. Hasselblad-inspired Colour: Natural Colour Solution (HNCS) smooth transitions
            # Smooth, uncompressed tonal curve without harsh clipping
            styled = np.power(styled, 0.98)
            # Gentle skin midtone warmth (+2% red, +1% yellow)
            styled[:, :, 0] += 0.02 * skin_mask[:, :, 0]
            styled[:, :, 1] += 0.01 * skin_mask[:, :, 0]

        elif profile == ColorProfile.CINEMATIC:
            # 5. Cinematic: 35mm film curve, teal shadows / amber highlights
            styled = np.power(styled, 1.12)
            sh_mask = np.clip(1.0 - luma * 1.6, 0.0, 1.0)[:, :, np.newaxis]
            hl_mask = np.clip((luma - 0.45) * 1.8, 0.0, 1.0)[:, :, np.newaxis]
            # Push shadows teal (cyan + blue)
            styled[:, :, 0] -= sh_mask[:, :, 0] * 0.04
            styled[:, :, 1] += sh_mask[:, :, 0] * 0.02
            styled[:, :, 2] += sh_mask[:, :, 0] * 0.05
            # Push highlights amber
            styled[:, :, 0] += hl_mask[:, :, 0] * 0.06
            styled[:, :, 1] += hl_mask[:, :, 0] * 0.03
            styled[:, :, 2] -= hl_mask[:, :, 0] * 0.04

        elif profile == ColorProfile.STUDIO_PORTRAIT:
            # 6. Studio Portrait: Diffuse key illumination, balanced porcelain glow
            styled = styled / (1.0 + styled * 0.10) * 1.10
            # Gentle lift on shadows for clean catchlights
            styled += (1.0 - luma[:, :, np.newaxis]) * 0.04

        elif profile == ColorProfile.WARM_PORTRAIT:
            # 7. Warm Portrait: Golden hour warmth, sunset skin radiance
            styled[:, :, 0] += 0.05
            styled[:, :, 1] += 0.02
            styled[:, :, 2] -= 0.03

        elif profile == ColorProfile.COOL_PORTRAIT:
            # 8. Cool Portrait: Crisp editorial cool tones, clean whites
            styled[:, :, 0] -= 0.02
            styled[:, :, 1] += 0.01
            styled[:, :, 2] += 0.05

        elif profile == ColorProfile.NEUTRAL_EDITORIAL:
            # 9. Neutral Editorial: Matte black point, high-fashion neutral balance
            # Matte black-point lift
            styled = np.clip(styled * 0.94 + 0.03, 0.0, 1.0)
            styled = np.power(styled, 1.08)

        # Apply skin tone protection if enabled: retain original natural complexion
        if skin_protection:
            skin_blend = skin_mask * 0.65
            styled = styled * (1.0 - skin_blend) + norm * skin_blend

        # Final alpha blend based on user intensity slider
        final_norm = norm * (1.0 - alpha) + styled * alpha
        out_arr = np.clip(final_norm * 255.0, 0.0, 255.0).astype(np.uint8)

        return Image.fromarray(out_arr), {
            "profile": profile.value,
            "intensity": round(alpha * 100.0, 1),
            "skin_protection_active": skin_protection,
            "applied": True,
        }
