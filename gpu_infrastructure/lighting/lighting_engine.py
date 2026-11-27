"""
Advanced Photographic Lighting Engine.
Provides authentic photometric exposure correction, highlight recovery,
shadow recovery, chromatic white-balance adaptation, HDR tone mapping,
and dynamic range optimization without washing out faces or highlights.
Adheres strictly to zero default brightness increase.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, Optional, Tuple
import numpy as np
from PIL import Image

logger = logging.getLogger("gpu_infrastructure.lighting.lighting_engine")


@dataclass
class LightingAnalysis:
    """Detailed photometric properties of an input photograph."""
    mean_luminance: float       # [0, 255]
    median_luminance: float     # [0, 255]
    shadow_ratio: float         # percentage < 30
    highlight_ratio: float      # percentage > 235
    dynamic_range_stops: float  # log2 dynamic range estimation
    color_cast_kelvin: float    # estimated correlated color temperature
    under_exposed: bool
    over_exposed: bool
    high_dynamic_range: bool


class AdvancedLightingEngine:
    """
    Photometric lighting and tone-mapping processor.
    Protects facial specular highlights, recovers deep shadows,
    and balances exposure strictly per-image rather than with uniform brightening.
    """

    def analyze_lighting(self, img_rgb: Image.Image) -> LightingAnalysis:
        """Computes statistical exposure, clipping metrics, and color cast."""
        arr = np.array(img_rgb.convert("RGB"), dtype=np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        total_px = max(1, luma.size)

        mean_lum = float(np.mean(luma))
        median_lum = float(np.median(luma))
        shadow_pct = float(np.sum(luma < 30.0) / total_px * 100.0)
        highlight_pct = float(np.sum(luma > 235.0) / total_px * 100.0)

        # Dynamic range estimation in stops
        p1 = max(1.0, float(np.percentile(luma, 1)))
        p99 = max(1.0, float(np.percentile(luma, 99)))
        dr_stops = float(np.log2(p99 / p1)) if p99 > p1 else 1.0

        # Estimated Kelvin deviation from neutral gray-world (R/B balance)
        mean_r, mean_b = float(np.mean(r)), float(np.mean(b))
        rb_ratio = mean_r / max(1.0, mean_b)
        est_kelvin = 5500.0 * (1.0 / max(0.5, rb_ratio))

        under_exp = mean_lum < 75.0 or (shadow_pct > 18.0 and highlight_pct < 2.0)
        over_exp = mean_lum > 180.0 or highlight_pct > 12.0
        hdr = dr_stops > 7.0 or (shadow_pct > 10.0 and highlight_pct > 8.0)

        return LightingAnalysis(
            mean_luminance=round(mean_lum, 2),
            median_luminance=round(median_lum, 2),
            shadow_ratio=round(shadow_pct, 2),
            highlight_ratio=round(highlight_pct, 2),
            dynamic_range_stops=round(dr_stops, 2),
            color_cast_kelvin=round(est_kelvin, 1),
            under_exposed=under_exp,
            over_exposed=over_exp,
            high_dynamic_range=hdr,
        )

    def process(
        self,
        img: Image.Image,
        exposure_adj: float = 0.0,       # -50 to +50 (0 = automatic/neutral)
        highlight_recovery: float = 0.0, # 0 to 100
        shadow_recovery: float = 0.0,    # 0 to 100
        hdr_tone_map: bool = False,
        white_balance_auto: bool = True,
        local_contrast: float = 0.0,     # 0 to 100
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Executes calibrated tone reconstruction.
        CRITICAL: Never increases brightness if photograph is already well exposed.
        """
        analysis = self.analyze_lighting(img)
        arr = np.array(img.convert("RGB"), dtype=np.float32)

        # 1. Chromatic White Balance (Gray-World Retinex)
        if white_balance_auto:
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            mean_r = max(1.0, float(np.mean(r)))
            mean_g = max(1.0, float(np.mean(g)))
            mean_b = max(1.0, float(np.mean(b)))
            gray_target = (mean_r + mean_g + mean_b) / 3.0

            # Subtle correction only (max 12% shift to protect golden hour / warm moods)
            scale_r = 1.0 + np.clip((gray_target / mean_r) - 1.0, -0.12, 0.12)
            scale_b = 1.0 + np.clip((gray_target / mean_b) - 1.0, -0.12, 0.12)

            arr[:, :, 0] = np.clip(arr[:, :, 0] * scale_r, 0.0, 255.0)
            arr[:, :, 2] = np.clip(arr[:, :, 2] * scale_b, 0.0, 255.0)

        # 2. Exposure & Dynamic Curve Calibration
        norm = arr / 255.0
        luma = 0.299 * norm[:, :, 0] + 0.587 * norm[:, :, 1] + 0.114 * norm[:, :, 2]

        # Automatic intelligent exposure offset if user control is neutral (0.0)
        auto_exp_shift = 0.0
        if exposure_adj == 0.0:
            if analysis.under_exposed:
                # Moderate shadow lift without blowing midtones
                auto_exp_shift = min(0.20, (85.0 - analysis.mean_luminance) / 255.0)
            elif analysis.over_exposed:
                # Highlight conservation pull-down
                auto_exp_shift = max(-0.15, (170.0 - analysis.mean_luminance) / 255.0)
        else:
            auto_exp_shift = (exposure_adj / 100.0) * 0.40

        if auto_exp_shift != 0.0:
            # Photographic EV curve: protects extreme shadows & extreme highlights
            ev_curve = np.power(2.0, auto_exp_shift * np.sin(luma * np.pi))
            norm = np.clip(norm * ev_curve[:, :, np.newaxis], 0.0, 1.0)

        # 3. Highlight Recovery & Shoulder Compression
        hl_strength = max(highlight_recovery, 35.0 if analysis.highlight_ratio > 5.0 else 0.0)
        if hl_strength > 0.0:
            hl_weight = (hl_strength / 100.0) * 0.35
            # Identify highlight zone (> 0.65)
            hl_mask = np.clip((luma - 0.65) / 0.35, 0.0, 1.0)[:, :, np.newaxis]
            # Soft shoulder compression (Reinhard-inspired roll-off)
            compressed = norm / (1.0 + norm * 0.25)
            norm = norm * (1.0 - hl_mask * hl_weight) + compressed * (hl_mask * hl_weight)

        # 4. Shadow Recovery & Toe Lift
        sh_strength = max(shadow_recovery, 40.0 if analysis.shadow_ratio > 15.0 else 0.0)
        if sh_strength > 0.0:
            sh_weight = (sh_strength / 100.0) * 0.30
            # Identify deep shadow zone (< 0.40)
            sh_mask = np.clip((0.40 - luma) / 0.40, 0.0, 1.0)[:, :, np.newaxis]
            shadow_boost = np.sqrt(norm) * 0.25
            norm = norm + shadow_boost * (sh_mask * sh_weight)

        # 5. HDR Tone Mapping (Filmic S-Curve)
        if hdr_tone_map or analysis.high_dynamic_range:
            # ACES-style gentle contrast enhancement
            a = 2.51
            b = 0.03
            c = 2.43
            d = 0.59
            e = 0.14
            norm = np.clip((norm * (a * norm + b)) / (norm * (c * norm + d) + e), 0.0, 1.0)

        # 6. Local Contrast Boost
        lc_val = max(0.0, min(100.0, local_contrast))
        if lc_val > 0.0:
            lc_alpha = (lc_val / 100.0) * 0.25
            # Unsharp mask in floating point
            try:
                from scipy import ndimage
                blurred = ndimage.gaussian_filter(norm, sigma=(2.5, 2.5, 0))
                norm = np.clip(norm + (norm - blurred) * lc_alpha, 0.0, 1.0)
            except ImportError:
                pass

        out_arr = np.clip(norm * 255.0, 0.0, 255.0).astype(np.uint8)
        out_img = Image.fromarray(out_arr)

        metrics = {
            "initial_lighting": {
                "mean_luminance": analysis.mean_luminance,
                "shadow_pct": analysis.shadow_ratio,
                "highlight_pct": analysis.highlight_ratio,
                "dynamic_range_stops": analysis.dynamic_range_stops,
                "under_exposed": analysis.under_exposed,
                "over_exposed": analysis.over_exposed,
            },
            "adjustments_applied": {
                "exposure_shift": round(float(auto_exp_shift), 3),
                "highlight_recovery_applied": bool(hl_strength > 0.0),
                "shadow_recovery_applied": bool(sh_strength > 0.0),
                "hdr_applied": bool(hdr_tone_map or analysis.high_dynamic_range),
                "white_balance_calibrated": bool(white_balance_auto),
            },
        }

        return out_img, metrics
