"""
AI Clarity Engine V2 — Master Autonomous Pipeline Orchestrator.
Orchestrates:
  1. Smart Auto Defect Classification (blur, noise, exposure, compression, faces).
  2. Advanced Lighting Engine (exposure calibration, highlight/shadow recovery, HDR).
  3. Extreme Face Restoration Ensemble (GFPGAN + CodeFormer + RestoreFormer).
  4. Extreme Super-Resolution (Real-ESRGAN + SwinIR 2x/4x with tiling).
  5. Men's, Women's, and Universal Portrait Studio Engine.
  6. Professional Colour Science (9 Photographic Profiles).
  7. Advanced Quality Gate with PSNR, SSIM, LPIPS, and Degradation Rejection.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from ..model_adapters import (
    BackgroundRemoverAdapter,
    BokehBlurAdapter,
    ImageDenoiserAdapter,
    LowLightAdapter,
    MotionDeblurAdapter,
    OldPhotoRestorationAdapter,
    PhotoColorizerAdapter,
    QualityAnalyzerAdapter,
    JpegDeblockAdapter,
)
from ..lighting import AdvancedLightingEngine
from ..color_science import ColorProfile, ProfessionalColorEngine
from ..portrait_studio import PortraitProfile, PortraitStudioEngine
from ..face_restoration import ExtremeFaceRestorer, FaceRestoreModel
from ..super_resolution import ExtremeSuperResolutionEngine, SuperResModel
from ..quality_evaluator import AdvancedQualityEngine
from ..inference.neural_engine import QualityValidator


class PipelineOrchestrator:
    """
    AI Clarity Engine V2 — Production Master Orchestrator.
    Executes automated defect detection, dynamic model routing, and staged pipeline processing.
    """

    def __init__(self):
        self.analyzer = QualityAnalyzerAdapter()
        self.lighting = AdvancedLightingEngine()
        self.color_engine = ProfessionalColorEngine()
        self.portrait_studio = PortraitStudioEngine()
        self.extreme_face = ExtremeFaceRestorer()
        self.extreme_sr = ExtremeSuperResolutionEngine()
        self.quality_engine = AdvancedQualityEngine()
        self.deblocker = JpegDeblockAdapter()
        self.denoiser = ImageDenoiserAdapter()
        self.deblurrer = MotionDeblurAdapter()
        self.colorizer = PhotoColorizerAdapter()
        self.lowlight = LowLightAdapter()
        self.bokeh = BokehBlurAdapter()

    def run_auto_enhance(
        self,
        img: Image.Image,
        target_scale: int = 4,
        allow_face_restore: bool = True,
        bokeh_radius: int = 0,
        portrait_profile: str = "universal",
        color_profile: str = "natural_pro",
        # Advanced granular controls (0-100)
        ai_clarity: int = 80,
        face_restoration_strength: int = 80,
        detail_recovery: int = 85,
        skin_texture_fidelity: int = 85,
        noise_reduction_strength: int = 0,
        exposure_adj: int = 0,
        color_fidelity: int = 90,
        sharpness: int = 80,
        identity_preservation: int = 85,
        **kwargs,
    ) -> Tuple[Image.Image, List[str], Dict[str, Any]]:
        """
        Executes fully autonomous AI clarity pipeline V2.
        Analyzes photo, repairs defects, applies restorative models,
        and benchmarks quality with strict degradation rejection.
        """
        start_time = time.time()
        pipeline_log: List[str] = []
        current_img = img.copy()

        # Step 1: Pre-Inference Quality Assessment
        _, analysis = self.analyzer.execute(current_img)
        pipeline_log.append("Quality Assessment & Defect Classification")

        # Step 2: Advanced Lighting Calibration & Exposure Correction
        # Never increase brightness by default; protect highlights and avoid washed-out faces
        lighting_analysis = self.lighting.analyze_lighting(current_img)
        if lighting_analysis.under_exposed or lighting_analysis.over_exposed or exposure_adj != 0:
            current_img, l_metrics = self.lighting.process(
                current_img,
                exposure_adj=float(exposure_adj),
                highlight_recovery=40.0 if lighting_analysis.highlight_ratio > 4.0 else 0.0,
                shadow_recovery=35.0 if lighting_analysis.shadow_ratio > 15.0 else 0.0,
                hdr_tone_map=lighting_analysis.high_dynamic_range,
                white_balance_auto=True,
            )
            pipeline_log.append("Advanced Lighting Engine (Photometric Curve & Highlight Shield)")

        # Step 3: JPEG Artifact Deblock (if compression artifacts detected)
        if analysis.get("blur_score", 0.0) < 60.0 or analysis.get("noise_score", 0.0) > 7.0:
            current_img, _ = self.deblocker.execute(current_img, strength=1.0)
            pipeline_log.append("SwinIR JPEG Artifact & Ringing Suppression")

        # Step 4: Denoise if sensor noise detected or requested
        if analysis.get("is_noisy", False) or noise_reduction_strength > 0:
            h_val = 6.0 if noise_reduction_strength == 0 else (noise_reduction_strength / 100.0) * 10.0
            current_img, _ = self.denoiser.execute(current_img, h_luminance=h_val)
            pipeline_log.append("Multi-Scale Sensor Denoiser")

        # Step 5: Motion Deblurring if blur detected
        if analysis.get("is_blurry", False):
            current_img, _ = self.deblurrer.execute(current_img, strength=1.15)
            pipeline_log.append("NAFNet Motion Deblur")

        # Step 6: B&W Deep Spectrum Colorizer (if monochrome)
        if analysis.get("is_monochrome", False):
            current_img, _ = self.colorizer.execute(current_img, saturation=1.15)
            pipeline_log.append("Deep Spectrum B&W Colorizer")

        # Step 7: Optical Bokeh Blur (if requested)
        if bokeh_radius > 0:
            current_img, _ = self.bokeh.execute(current_img, radius=bokeh_radius)
            pipeline_log.append(f"DSLR Background Bokeh Blur ({bokeh_radius}px)")

        # Step 8: Extreme Face Restoration Ensemble (GFPGAN + CodeFormer + RestoreFormer)
        face_count = int(analysis.get("face_count", 0))
        if allow_face_restore and face_count > 0:
            current_img, face_met = self.extreme_face.restore_faces(
                current_img,
                model_type=FaceRestoreModel.AUTO_ENSEMBLE,
                user_fidelity=float(face_restoration_strength),
                identity_weight=float(identity_preservation),
                adaptive_strength=True,
            )
            pipeline_log.append(f"Extreme Face Restoration Ensemble ({face_count} faces restored with CodeFormer Identity Guard)")

        # Step 9: Extreme Super-Resolution (Real-ESRGAN + SwinIR 2x/4x)
        if target_scale > 1:
            current_img, sr_met = self.extreme_sr.upscale(
                current_img,
                scale=target_scale,
                model=SuperResModel.ENSEMBLE_SR,
                detail_recovery=float(detail_recovery),
            )
            pipeline_log.append(f"Extreme Super-Resolution ({sr_met['scale']} Real-ESRGAN + SwinIR)")

        # Step 10: Men's, Women's, or Universal Portrait Studio Processing
        try:
            pp = PortraitProfile(portrait_profile.lower())
        except ValueError:
            pp = PortraitProfile.UNIVERSAL

        current_img, p_metrics = self.portrait_studio.process_portrait(
            current_img,
            profile=pp,
            skin_texture_fidelity=float(skin_texture_fidelity),
            feature_clarity=float(sharpness),
            subtle_radiance=25.0 if pp == PortraitProfile.WOMEN else 0.0,
            clothing_recovery=True,
        )
        if pp == PortraitProfile.MEN:
            pipeline_log.append("Men's Portrait Studio (Beard, Hair & Contour Definition)")
        elif pp == PortraitProfile.WOMEN:
            pipeline_log.append("Women's Portrait Studio (Eyelash, Eyebrow & Complexion Precision)")
        else:
            pipeline_log.append("Universal Natural Portrait (Identity & Micro-Pore Preservation)")

        # Step 11: Professional Colour Science
        try:
            cp = ColorProfile(color_profile.lower())
        except ValueError:
            cp = ColorProfile.NATURAL_PRO

        current_img, c_metrics = self.color_engine.apply_profile(
            current_img,
            profile=cp,
            intensity=float(color_fidelity),
            skin_protection=True,
        )
        pipeline_log.append(f"Professional Colour Science ({cp.name.replace('_', ' ').title()})")

        # Step 12: Degradation Rejection Quality Guard
        duration = round(float(time.time() - start_time), 2)
        final_img, is_degraded, guard_info = QualityValidator.guard_against_degradation(img, current_img)
        if is_degraded:
            pipeline_log.append(f"Quality Guard Active: Candidate preserved with native camera detail lift ({guard_info['rejection_reason']})")

        # Step 13: Scientific Quality Evaluation (PSNR, SSIM, LPIPS, Identity)
        benchmarks = self.quality_engine.evaluate(img, final_img, duration_sec=duration)

        telemetry = {
            "pipeline_steps": [str(s) for s in pipeline_log],
            "analysis": analysis,
            "benchmarks": benchmarks,
            "portrait_profile": pp.value,
            "color_profile": cp.value,
            "duration_sec": duration,
            "guard_info": guard_info,
        }

        return final_img, pipeline_log, telemetry


# Master Singleton Orchestrator
orchestrator = PipelineOrchestrator()
