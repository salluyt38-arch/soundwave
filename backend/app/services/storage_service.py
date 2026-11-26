"""
APEX Storage Service
Manages secure temporary file storage with automatic 10-minute artifact expiration.
"""

import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple
from ..config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    ARTIFACT_EXPIRY_SECONDS,
    MAX_UPLOAD_SIZE_BYTES,
    OUTPUTS_DIR,
    UPLOADS_DIR,
)


class StorageService:
    """
    Manages local filesystem artifacts with strict zero-leakage retention policies.
    """

    @classmethod
    def save_upload(cls, file_bytes: bytes, original_filename: str) -> Tuple[str, Path]:
        """
        Validates and saves uploaded file bytes to temporary uploads directory.
        Returns (file_id, file_path).
        """
        if not file_bytes:
            raise ValueError("Upload payload is empty.")

        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"Payload exceeds max allowed size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.")

        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = ".jpg"

        file_id = f"upload_{uuid.uuid4().hex[:12]}"
        file_path = UPLOADS_DIR / f"{file_id}{ext}"

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Trigger automatic cleanup of expired files
        cls.cleanup_expired_artifacts()

        return file_id, file_path

    @classmethod
    def save_output(cls, file_bytes: bytes, job_id: str, format_ext: str = ".jpg") -> Path:
        """
        Saves enhanced output file bytes to outputs directory.
        """
        if not format_ext.startswith("."):
            format_ext = f".{format_ext}"

        out_path = OUTPUTS_DIR / f"{job_id}{format_ext}"
        with open(out_path, "wb") as f:
            f.write(file_bytes)

        return out_path

    @classmethod
    def get_upload_path(cls, file_id: str) -> Optional[Path]:
        """Finds uploaded file by file_id."""
        for ext in ALLOWED_EXTENSIONS:
            p = UPLOADS_DIR / f"{file_id}{ext}"
            if p.exists():
                return p
        return None

    @classmethod
    def get_output_path(cls, job_id: str) -> Optional[Path]:
        """Finds completed output file by job_id."""
        for ext in [".jpg", ".png", ".webp", ".jpeg"]:
            p = OUTPUTS_DIR / f"{job_id}{ext}"
            if p.exists():
                return p
        return None

    @classmethod
    def cleanup_expired_artifacts(cls) -> int:
        """
        Purges temporary uploads and outputs older than ARTIFACT_EXPIRY_SECONDS (10 mins).
        Returns number of deleted files.
        """
        now = time.time()
        purged = 0

        for folder in [UPLOADS_DIR, OUTPUTS_DIR]:
            try:
                for item in folder.iterdir():
                    if item.is_file():
                        age = now - item.stat().st_mtime
                        if age > ARTIFACT_EXPIRY_SECONDS:
                            try:
                                item.unlink(missing_ok=True)
                                purged += 1
                            except Exception:
                                pass
            except Exception:
                pass

        return purged
