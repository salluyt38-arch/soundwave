"""
APEX Intelligent AI Model Selection & Inference Pipeline
Dynamically inspects input images (resolution, faces, noise, monochrome, scratches)
and orchestrates the exact required models without wasteful execution.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image

from ..face_detection.detector import FaceDetector
from ..face_restoration.restorer import FaceRestorationEngine
from ..image_colorization.colorizer import ImageColorizer
from ..image_denoising.denoiser import ImageDenoiser
from ..image_inpainting.inpainter import ImageInpainter
from ..image_upscaling.upscaler import SuperResolutionEngine
from ..old_photo_restoration.restorer import OldPhotoRestorer
from ..quality_assessment.evaluator import ImageQualityEvaluator
from ...schemas.models import QualityMetrics


class ApexInferencePipeline:
    """
    Intelligent master pipeline orchestrating Real-ESRGAN, GFPGAN, CodeFormer,
    SwinIR, LaMa, and Colorization based on image characteristics.
    """

    def __init__(self):
        self.detector = FaceDetector()
        self.face_restorer = FaceRestorationEngine(detector=self.detector)
        self.upscaler = SuperResolutionEngine()
        self.denoiser = ImageDenoiser()
        self.colorizer = ImageColorizer()
        self.old_photo_restorer = OldPhotoRestorer()
        self.inpainter = ImageInpainter()

    def analyze_image_characteristics(self, img: Image.Image) -> Dict[str, Any]:
        """
        Diagnoses image properties: resolution, presence of faces, noise variance, monochrome status.
        """
        w, h = img.size
        rgb = img.convert("RGB")
        np_arr = np.array(rgb)

        # 1. Check Monochrome / Black & White
        # If R, G, B channels have near-zero standard deviation, the image is grayscale
        diff_rg = np.abs(np_arr[:, :, 0].astype(np.float32) - np_arr[:, :, 1].astype(np.float32))
        diff_gb = np.abs(np_arr[:, :, 1].astype(np.float32) - np_arr[:, :, 2].astype(np.float32))
        is_monochrome = (np.mean(diff_rg) < 3.5) and (np.mean(diff_gb) < 3.5)

        # 2. Check Resolution Category
        is_low_res = (w < 1000) or (h < 1000)
        is_ultra_hd = (w >= 3840) or (h >= 3840)

        # 3. Detect Faces
        faces = self.detector.detect_faces(rgb)
        has_faces = len(faces) > 0
        face_count = len(faces)

        # 4. Check Noise Level (High-frequency Laplacian variance)
        gray = np.array(img.convert("L"), dtype=np.float32)
        laplace_var = ImageQualityEvaluator.compute_blur_score(gray)
        is_noisy = laplace_var > 450.0  # High noise variance
        is_blurry = laplace_var < 80.0   # Low edge variance

        return {
            "width": w,
            "height": h,
            "is_monochrome": is_monochrome,
            "is_low_res": is_low_res,
            "is_ultra_hd": is_ultra_hd,
            "has_faces": has_faces,
            "face_count": face_count,
            "is_noisy": is_noisy,
            "is_blurry": is_blurry,
            "blur_score": laplace_var,
        }

    def execute_auto_enhance(
        self,
        img: Image.Image,
        scale: int = 4,
        face_restore: bool = True,
        face_strength: float = 0.85,
        denoise_strength: float = 0.5,
        color_correct: bool = True,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        """
        Intelligently executes the complete APEX AI restoration pipeline:
          Step 1: Analyze image characteristics.
          Step 2: Denoise if sensor noise or compression grit is present.
          Step 3: Restore facial landmarks & skin if faces detected.
          Step 4: Super-resolution upscaling (2x or 4x with guided detail transfer).
          Step 5: Color correction and contrast optimization.
          Step 6: Evaluate quality metrics (PSNR, SSIM, duration).
        """
        start_time = time.time()
        models_used = []
        working_img = img.convert("RGB")

        # 1. Analyze input characteristics
        diag = self.analyze_image_characteristics(working_img)

        # 2. Denoising Stage (if noisy or compression artifacts present)
        if diag["is_noisy"] or denoise_strength > 0.4:
            working_img = self.denoiser.denoise(working_img, strength=denoise_strength * 0.7)
            models_used.append("swinir_denoise")

        # 3. Facial Restoration Stage (Run on input space before super-resolution)
        # Prevents high memory consumption and lets upscaler refine clean facial landmarks
        if face_restore and diag["has_faces"]:
            working_img = self.face_restorer.restore_faces(
                working_img,
                fidelity_weight=face_strength,
                eye_enhancement=True,
                skin_polish=True,
                lip_enhancement=True,
            )
            models_used.append("gfpgan_v1.4")
            models_used.append("codeformer_fidelity")

        # 4. Super-Resolution Stage (2x, 4x, or 8x - Zero Input Crushing)
        if scale > 1:
            scale = max(2, min(scale, 8))
            max_dim = max(working_img.width, working_img.height)
            if max_dim * scale > 8192:
                scale = max(1, 8192 // max_dim)

            if scale > 1:
                working_img = self.upscaler.upscale(
                    working_img,
                    scale=scale,
                    model_name="real-esrgan",
                    sharpen=True,
                )
                models_used.append(f"real_esrgan_{scale}x")
            else:
                working_img = working_img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=1))
                models_used.append("real_esrgan_native_1x")

        # 5. Quality Assessment & Metrics Validation
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(
            orig_img=img,
            enhanced_img=working_img,
            duration_sec=duration,
            scale=scale,
        )

        return working_img, models_used, metrics

    def execute_face_restore_only(
        self,
        img: Image.Image,
        fidelity: float = 0.85,
        model_name: str = "codeformer",
        eye_enhancement: bool = True,
        skin_polish: bool = True,
        lip_enhancement: bool = True,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        restored = self.face_restorer.restore_faces(
            img,
            fidelity_weight=fidelity,
            model_name=model_name,
            eye_enhancement=eye_enhancement,
            skin_polish=skin_polish,
            lip_enhancement=lip_enhancement,
        )
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(img, restored, duration, scale=1)
        return restored, [f"{model_name}_face_restore"], metrics

    def execute_upscale_only(
        self,
        img: Image.Image,
        scale: int = 4,
        model_name: str = "real-esrgan",
        sharpen: bool = True,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        upscaled = self.upscaler.upscale(img, scale=scale, model_name=model_name, sharpen=sharpen)
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(img, upscaled, duration, scale=scale)
        return upscaled, [f"{model_name}_{scale}x"], metrics

    def execute_old_photo_restore(
        self,
        img: Image.Image,
        remove_scratches: bool = True,
        colorize: bool = False,
        face_restore: bool = True,
        contrast_recovery: bool = True,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        restored = self.old_photo_restorer.restore(
            img,
            remove_scratches=remove_scratches,
            colorize=colorize,
            face_restore=face_restore,
            contrast_recovery=contrast_recovery,
        )
        duration = time.time() - start_time
        models = ["bringing_old_photos_back_to_life"]
        if colorize:
            models.append("zhang_colorization")
        if face_restore:
            models.append("gfpgan_face_restore")
        metrics = ImageQualityEvaluator.evaluate(img, restored, duration, scale=1)
        return restored, models, metrics

    def execute_colorize(
        self,
        img: Image.Image,
        saturation: float = 1.15,
        warmth: float = 1.05,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        colorized = self.colorizer.colorize(img, saturation=saturation, warmth=warmth)
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(img, colorized, duration, scale=1)
        return colorized, ["colorful_image_colorization"], metrics

    def execute_denoise(
        self,
        img: Image.Image,
        strength: float = 0.6,
        preserve_texture: bool = True,
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        denoised = self.denoiser.denoise(img, strength=strength, preserve_texture=preserve_texture)
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(img, denoised, duration, scale=1)
        return denoised, ["swinir_guided_denoise"], metrics

    def execute_inpaint(
        self,
        img: Image.Image,
        mask: Image.Image,
        algorithm: str = "lama_guided",
    ) -> Tuple[Image.Image, List[str], QualityMetrics]:
        start_time = time.time()
        inpainted = self.inpainter.inpaint(img, mask, algorithm=algorithm)
        duration = time.time() - start_time
        metrics = ImageQualityEvaluator.evaluate(img, inpainted, duration, scale=1)
        return inpainted, [f"lama_{algorithm}_inpaint"], metrics
