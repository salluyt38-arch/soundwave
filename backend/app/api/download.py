"""
Job Polling, Result Delivery, Artifact Download & Additional AI Endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from ..schemas.models import DenoiseRequest, InpaintRequest, JobResponse
from ..services.enhancement_service import EnhancementService
from ..services.job_service import JobService
from ..services.storage_service import StorageService

router = APIRouter(tags=["Jobs & Downloads"])
enhancer = EnhancementService()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Polls real-time job state, progress percentage, and quality metrics."""
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancels an active or queued job."""
    success = JobService.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Could not cancel job '{job_id}'.")
    return {"status": "cancelled", "job_id": job_id}


@router.get("/download/{job_id}")
async def download_result(job_id: str, format: str = "jpg"):
    """Downloads the enhanced high-resolution image artifact."""
    file_path = StorageService.get_output_path(job_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact for job '{job_id}' expired or not found.")

    ext = file_path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    filename = f"APEX_Enhanced_{job_id}{ext}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/download/preview/{file_id}")
async def get_uploaded_preview(file_id: str):
    """Streams original uploaded file for browser display."""
    file_path = StorageService.get_upload_path(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Upload '{file_id}' not found.")

    ext = file_path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(path=str(file_path), media_type=media_type)


@router.post("/denoise", response_model=JobResponse)
async def denoise_image(request: DenoiseRequest):
    """Denoises sensor grain and ISO noise."""
    try:
        return enhancer.run_denoise(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inpaint", response_model=JobResponse)
async def inpaint_image(request: InpaintRequest):
    """Inpaints and removes objects from masked regions."""
    try:
        return enhancer.run_inpaint(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
