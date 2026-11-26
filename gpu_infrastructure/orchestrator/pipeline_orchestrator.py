"""
Intelligent AI Pipeline Orchestrator for Adobe Studio Pro.
Executes automated defect classification, dynamic model routing, and staged pipeline processing.
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

    def run_auto_enhance(
        self,
        img: Image.Image,
        target_scale: int = 4,
        allow_face_restore: bool = True,
        bokeh_radius: int = 0,
    ) -> Tuple[Image.Image, List[str], Dict[str, Any]]:
        """
        Executes fully autonomous AI enhancement pipeline.
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
        face_count = analysis.get("face_count", 0)
        if allow_face_restore and face_count > 0:
            current_img, _ = self.face_restorer.execute(current_img, fidelity_weight=0.85)
            pipeline_log.append(f"GFPGAN Face Beauty ({face_count} faces restored)")

        # Step 8: Multi-Scale Super-Resolution
        current_img, sr_metrics = self.super_res.execute(current_img, scale=target_scale)
        pipeline_log.append(f"Real-ESRGAN {sr_metrics['effective_scale']} Super-Resolution")

        # Step 9: Final Quality Control Benchmarking
        duration = round(time.time() - start_time, 2)
        bench = BenchmarkMetrics.benchmark_run(img, current_img, duration)

        telemetry = {
            "pipeline_steps": pipeline_log,
            "analysis": analysis,
            "benchmarks": bench,
            "duration_sec": duration,
        }

        return current_img, pipeline_log, telemetry


# Singleton orchestrator
orchestrator = PipelineOrchestrator()
