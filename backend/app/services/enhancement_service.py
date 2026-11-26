"""
APEX Enhancement Service
Orchestrates AI inference jobs, image persistence, and quality metric packaging.
"""

from pathlib import Path
from typing import Optional
from PIL import Image

from ..ai_engine.inference_pipeline.pipeline import ApexInferencePipeline
from ..schemas.models import (
    BaseEnhanceRequest,
    ColorizeRequest,
    DenoiseRequest,
    FaceRestoreRequest,
    InpaintRequest,
    JobResponse,
    JobStatus,
    OldPhotoRestoreRequest,
    UpscaleRequest,
)
from .image_service import ImageService
from .job_service import JobService
from .storage_service import StorageService


class EnhancementService:
    """
    Core business logic executing AI operations and saving output artifacts.
    """

    def __init__(self):
        self.pipeline = ApexInferencePipeline()

    def _resolve_image(self, image_b64: Optional[str], file_id: Optional[str]) -> Image.Image:
        """Resolves PIL Image from Base64 or previously uploaded file_id."""
        if file_id:
            file_path = StorageService.get_upload_path(file_id)
            if not file_path or not file_path.exists():
                raise FileNotFoundError(f"File ID '{file_id}' not found.")
            img = Image.open(file_path).convert("RGB")
            return img

        if image_b64:
            return ImageService.decode_image(image_b64)

        raise ValueError("Must provide either 'image' (base64) or 'file_id'.")

    def run_auto_enhance(self, req: BaseEnhanceRequest) -> JobResponse:
        job = JobService.create_job("auto_enhance")
        try:
            JobService.update_progress(job.job_id, 20, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 50)
            enhanced, models_used, metrics = self.pipeline.execute_auto_enhance(
                img=img,
                scale=req.scale,
                face_restore=req.face_restore,
                face_strength=req.face_strength,
                denoise_strength=req.denoise_strength,
                color_correct=req.color_correct,
            )

            JobService.update_progress(job.job_id, 85)
            # Save artifact
            out_bytes = ImageService.image_to_bytes(enhanced, "JPEG", quality=95)
            StorageService.save_output(out_bytes, job.job_id, ".jpg")

            out_b64 = ImageService.image_to_base64(enhanced, "JPEG", quality=95)
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_face_restore(self, req: FaceRestoreRequest) -> JobResponse:
        job = JobService.create_job("face_restore")
        try:
            JobService.update_progress(job.job_id, 25, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 65)
            enhanced, models_used, metrics = self.pipeline.execute_face_restore_only(
                img=img,
                fidelity=req.fidelity,
                model_name=req.model_name,
                eye_enhancement=req.eye_enhancement,
                skin_polish=req.skin_polish,
                lip_enhancement=req.lip_enhancement,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "JPEG", quality=95)
            StorageService.save_output(out_bytes, job.job_id, ".jpg")
            out_b64 = ImageService.image_to_base64(enhanced, "JPEG", quality=95)
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_upscale(self, req: UpscaleRequest) -> JobResponse:
        job = JobService.create_job("upscale")
        try:
            JobService.update_progress(job.job_id, 25, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 70)
            enhanced, models_used, metrics = self.pipeline.execute_upscale_only(
                img=img,
                scale=req.scale,
                model_name=req.model_name,
                sharpen=req.sharpen,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "PNG")
            StorageService.save_output(out_bytes, job.job_id, ".png")
            out_b64 = ImageService.image_to_base64(enhanced, "PNG")
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_old_photo_restore(self, req: OldPhotoRestoreRequest) -> JobResponse:
        job = JobService.create_job("old_photo_restore")
        try:
            JobService.update_progress(job.job_id, 20, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 65)
            enhanced, models_used, metrics = self.pipeline.execute_old_photo_restore(
                img=img,
                remove_scratches=req.remove_scratches,
                colorize=req.colorize,
                face_restore=req.face_restore,
                contrast_recovery=req.contrast_recovery,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "JPEG", quality=95)
            StorageService.save_output(out_bytes, job.job_id, ".jpg")
            out_b64 = ImageService.image_to_base64(enhanced, "JPEG", quality=95)
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_colorize(self, req: ColorizeRequest) -> JobResponse:
        job = JobService.create_job("colorize")
        try:
            JobService.update_progress(job.job_id, 30, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 75)
            enhanced, models_used, metrics = self.pipeline.execute_colorize(
                img=img,
                saturation=req.saturation,
                warmth=req.warmth,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "JPEG", quality=95)
            StorageService.save_output(out_bytes, job.job_id, ".jpg")
            out_b64 = ImageService.image_to_base64(enhanced, "JPEG", quality=95)
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_denoise(self, req: DenoiseRequest) -> JobResponse:
        job = JobService.create_job("denoise")
        try:
            JobService.update_progress(job.job_id, 30, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)

            JobService.update_progress(job.job_id, 75)
            enhanced, models_used, metrics = self.pipeline.execute_denoise(
                img=img,
                strength=req.strength,
                preserve_texture=req.preserve_texture,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "JPEG", quality=95)
            StorageService.save_output(out_bytes, job.job_id, ".jpg")
            out_b64 = ImageService.image_to_base64(enhanced, "JPEG", quality=95)
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise

    def run_inpaint(self, req: InpaintRequest) -> JobResponse:
        job = JobService.create_job("inpaint")
        try:
            JobService.update_progress(job.job_id, 25, JobStatus.PROCESSING)
            img = self._resolve_image(req.image, req.file_id)
            mask = ImageService.decode_image(req.mask)

            JobService.update_progress(job.job_id, 70)
            enhanced, models_used, metrics = self.pipeline.execute_inpaint(
                img=img,
                mask=mask,
                algorithm=req.algorithm,
            )

            out_bytes = ImageService.image_to_bytes(enhanced, "PNG")
            StorageService.save_output(out_bytes, job.job_id, ".png")
            out_b64 = ImageService.image_to_base64(enhanced, "PNG")
            result_url = f"/api/download/{job.job_id}"

            return JobService.complete_job(job.job_id, out_b64, metrics, models_used, result_url)
        except Exception as e:
            JobService.fail_job(job.job_id, str(e))
            raise
