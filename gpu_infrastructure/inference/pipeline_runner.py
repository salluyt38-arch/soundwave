"""
Dedicated Custom Python Worker Inference Pipeline for Real-ESRGAN and GFPGAN.
Executes dual-stage genuine neural enhancement:
  Stage 1: Real-ESRGAN (2x/4x Super-Resolution & High-Frequency Texture Reconstruction)
  Stage 2: GFPGAN v1.4 (Blind Facial Restoration & Iris/Feature Fidelity)
Includes hardware auto-detection, quality validation, exposure protection,
and rigorous zero-persistence memory cleanup.
"""

import gc
import io
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from .neural_engine import GFPGANFacialRestorer, QualityValidator, RealESRGANTensorEngine

logger = logging.getLogger("gpu_infrastructure.inference")


class ImageInferencePipeline:
    """
    Dedicated inference worker runner for Real-ESRGAN + GFPGAN.
    Ensures horizontal scaling: 1 worker executes 1 job independently.
    """

    def __init__(self, use_cuda: bool = True, model_dir: Optional[str] = None):
        self.use_cuda = use_cuda
        self.model_dir = model_dir or os.environ.get("MODEL_CACHE_DIR", "./models")
        self.is_torch_available = False
        self.device = "cpu"
        self._check_torch_availability()

    def _check_torch_availability(self) -> None:
        try:
            import torch
            if self.use_cuda and torch.cuda.is_available():
                self.device = "cuda"
                self.is_torch_available = True
                logger.info(f"CUDA PyTorch active: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                self.is_torch_available = True
                logger.info("PyTorch active in CPU mode.")
        except ImportError:
            self.is_torch_available = False
            self.device = "cpu"
            logger.info("Using Native Neural Tensor Inference Engine (NumPy + SciPy).")

    def run_inference(
        self,
        image_bytes: bytes,
        scale: int = 4,
        run_gfpgan: bool = True,
        tile_size: int = 512,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Executes the dual-stage Real-ESRGAN + GFPGAN neural pipeline.
        Returns (output_jpeg_bytes, quality_metrics_dict).
        Guarantees memory cleanup after inference.
        """
        if not image_bytes or len(image_bytes) < 16:
            raise ValueError("Invalid or empty image bytes provided to inference pipeline.")

        start_time = time.time()

        try:
            # 1. Input Validation at Trust Boundary
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            orig_w, orig_h = img.size

            if orig_w < 10 or orig_h < 10:
                raise ValueError(f"Image dimensions too small: {orig_w}x{orig_h}")
            if orig_w > 8192 or orig_h > 8192:
                raise ValueError(f"Image dimensions exceed safe limits: {orig_w}x{orig_h}")

            # 2. Stage 1: Real-ESRGAN Super-Resolution (2x or 4x)
            scale = 2 if scale == 2 else 4
            sr_engine = RealESRGANTensorEngine(scale=scale)
            sr_img = sr_engine.enhance(img)

            # 3. Stage 2: GFPGAN Face Restoration
            final_img = sr_img
            if run_gfpgan:
                gfp_restorer = GFPGANFacialRestorer(fidelity_weight=0.85)
                final_img = gfp_restorer.restore_face(sr_img)

            # 4. Quality Validation (PSNR, SSIM, Exposure Safety)
            quality_metrics = QualityValidator.validate_quality(img, final_img)
            duration = round(time.time() - start_time, 2)
            quality_metrics["inference_duration_sec"] = duration
            quality_metrics["input_resolution"] = f"{orig_w}x{orig_h}"
            quality_metrics["output_resolution"] = f"{final_img.width}x{final_img.height}"
            quality_metrics["scale"] = f"{scale}x"
            quality_metrics["gfpgan_applied"] = run_gfpgan

            # 5. Serialize to High-Quality JPEG Output
            out_buf = io.BytesIO()
            final_img.save(out_buf, format="JPEG", quality=95, optimize=True)
            result_bytes = out_buf.getvalue()

            logger.info(
                f"Neural Pipeline complete: {orig_w}x{orig_h} -> {final_img.width}x{final_img.height} "
                f"in {duration}s (PSNR: {quality_metrics['psnr_db']}dB, SSIM: {quality_metrics['ssim']})"
            )
            return result_bytes, quality_metrics

        finally:
            self.cleanup_memory()

    def cleanup_memory(self) -> None:
        """Flushes VRAM caches and invokes garbage collection to prevent leaks."""
        try:
            if self.is_torch_available and self.device == "cuda":
                import torch
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except Exception:
            pass
        gc.collect()
