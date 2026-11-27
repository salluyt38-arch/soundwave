"""
Intelligent AI Pipeline Orchestrator for Adobe Studio Pro.
Executes automated defect classification, dynamic model routing, and staged pipeline processing.
Performs complete autonomous backend enhancement: defect removal, GFPGAN face restoration,
Real-ESRGAN super-resolution, GPUPixel natural skin polish, and adaptive dynamic clarity.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image

from ..model_adapters import (
    BackgroundRemoverAdapter,
    BokehBlurAdapter,
    FaceRestorationAdapter,
    ImageDenoiserAdapter,
    LowLightAdapter,
    MotionDeblurAdapter,
    OldPhotoRestorationAdapter,
    PhotoColorizerAdapter,
    QualityAnalyzerAdapter,
    SuperResolutionAdapter,
)
from ..beauty import (
    FaceAnalyzer,
    GPUPixelEngine,
    IntelligentFilterEngine,
    PortraitFilterType,
    StylePreset,
)
from ..benchmarking.metrics import BenchmarkMetrics


class PipelineOrchestrator:
    """Intelligent pipeline router that analyzes image quality and chains optimal AI models."""

    def __init__(self):
        self.analyzer = QualityAnalyzerAdapter()
        self.super_res = SuperResolutionAdapter()
        self.face_restorer = FaceRestorationAdapter()
        self.bokeh = BokehBlurAdapter()
        self.deblurrer = MotionDeblurAdapter()
        self.denoiser = ImageDenoiserAdapter()
        self.lowlight = LowLightAdapter()
        self.bg_remover = BackgroundRemoverAdapter()
        self.old_photo = OldPhotoRestorationAdapter()
        self.colorizer = PhotoColorizerAdapter()
        self.face_analyzer = FaceAnalyzer()
        self.gpupixel = GPUPixelEngine()
        self.filter_engine = IntelligentFilterEngine()

    def run_auto_enhance(
        self,
        img: Image.Image,
        target_scale: int = 4,
        allow_face_restore: bool = True,
        bokeh_radius: int = 0,
        allow_beauty: bool = True,
        style_preset: str = "neutral",
    ) -> Tuple[Image.Image, List[str], Dict[str, Any]]:
        """
        Executes fully autonomous end-to-end AI enhancement pipeline in the backend.
        User simply passes photo; backend detects defects and outputs complete masterpiece.
        Returns (enhanced_img, applied_pipeline_steps, telemetry_metrics).
        """
        start_time = time.time()
        pipeline_log: List[str] = []
        current_img = img.copy()

        # Step 1: Pre-Inference Quality Assessment
        _, analysis = self.analyzer.execute(current_img)
        pipeline_log.append("Quality Assessment & Defect Classification")

        # Step 2: Low-Light shadow recovery if underexposed
        if analysis.get("is_low_light", False):
            current_img, _ = self.lowlight.execute(current_img, gamma=1.30)
            pipeline_log.append("Retinex Low-Light Illuminator")

        # Step 3: Denoise if high sensor noise detected
        if analysis.get("is_noisy", False):
            current_img, _ = self.denoiser.execute(current_img, h_luminance=6.0)
            pipeline_log.append("Multi-Scale Sensor Denoiser")

        # Step 4: Motion Deblurring if defocus/blur detected
        if analysis.get("is_blurry", False):
            current_img, _ = self.deblurrer.execute(current_img, strength=1.1)
            pipeline_log.append("NAFNet Motion Deblur")

        # Step 5: Colorize if image is monochrome
        if analysis.get("is_monochrome", False):
            current_img, _ = self.colorizer.execute(current_img, saturation=1.15)
            pipeline_log.append("Deep Spectrum B&W Colorizer")

        # Step 6: Optical Bokeh Blur if requested
        if bokeh_radius > 0:
            current_img, _ = self.bokeh.execute(current_img, radius=bokeh_radius)
            pipeline_log.append(f"DSLR Background Bokeh Blur ({bokeh_radius}px)")

        # Step 7: Face Restoration if faces detected and allowed
        face_count = int(analysis.get("face_count", 0))
        if allow_face_restore and face_count > 0:
            current_img, _ = self.face_restorer.execute(current_img, fidelity_weight=0.85)
            pipeline_log.append(f"GFPGAN Face Beauty ({face_count} faces restored)")

        # Step 8: Multi-Scale Super-Resolution
        current_img, sr_metrics = self.super_res.execute(current_img, scale=target_scale)
        pipeline_log.append(f"Real-ESRGAN {sr_metrics['effective_scale']} Super-Resolution")

        # Step 9: GPUPixel Natural Skin Polish & Face-Aware Enhancement
        if allow_beauty:
            try:
                face_analysis = self.face_analyzer.analyze(current_img)
                sp = StylePreset.NEUTRAL
                if style_preset == "men":
                    sp = StylePreset.MEN
                elif style_preset == "women":
                    sp = StylePreset.WOMEN

                if len(face_analysis.faces) > 0 or face_count > 0:
                    current_img, _ = self.gpupixel.apply_beauty_effects(
                        current_img,
                        face_analysis,
                        smooth_intensity=25,  # Natural skin smoothing (preserves 100% micro-pores)
                        whiten_intensity=16,  # Gentle radiance lift
                        tone_balance=12,      # Porcelain tone balance
                    )
                    pipeline_log.append("GPUPixel Intelligent Skin Polish & Radiance")

                    # Step 10: Adaptive Natural Portrait Clarity Filter
                    current_img, _ = self.filter_engine.apply_filter(
                        current_img,
                        face_analysis,
                        filter_type=PortraitFilterType.NATURAL_SKIN,
                        style_preset=sp,
                        intensity=55,
                    )
                    pipeline_log.append("Adaptive Natural Portrait Filter")
                else:
                    # Non-portrait photo (nature, landscape, architecture, objects): HD dynamic clarity
                    current_img, _ = self.filter_engine.apply_filter(
                        current_img,
                        face_analysis,
                        filter_type=PortraitFilterType.HD_PORTRAIT,
                        style_preset=StylePreset.NEUTRAL,
                        intensity=35,
                    )
                    pipeline_log.append("Adaptive Ultra-HD Dynamic Clarity")
            except Exception:
                pass

        # Step 11: Final Quality Control Benchmarking
        duration = round(float(time.time() - start_time), 2)
        bench = BenchmarkMetrics.benchmark_run(img, current_img, duration)

        telemetry = {
            "pipeline_steps": [str(s) for s in pipeline_log],
            "analysis": analysis,
            "benchmarks": bench,
            "duration_sec": duration,
        }

        return current_img, pipeline_log, telemetry


# Singleton orchestrator
orchestrator = PipelineOrchestrator()
