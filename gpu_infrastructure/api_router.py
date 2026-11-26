"""
Standardized REST API Router for Adobe Studio Pro (/api/ai/* endpoints).
Handles request validation, payload decoding, adapter execution, and serialization.
"""

import base64
import io
import time
from typing import Any, Dict, Optional, Tuple
from PIL import Image

from .security.payload_guard import PayloadGuard
from .model_registry.catalog import registry
from .diagnostics.health_check import run_system_diagnostics
from .benchmarking.metrics import BenchmarkMetrics
from .model_adapters import (
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
from .orchestrator.pipeline_orchestrator import orchestrator


def _extract_image_payload(body: Dict[str, Any]) -> Tuple[Optional[Image.Image], Optional[str]]:
    raw_bytes = None
    if "image_bytes" in body and isinstance(body["image_bytes"], bytes):
        raw_bytes = body["image_bytes"]
    else:
        b64_str = str(body.get("image", "")).strip()
        if b64_str:
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(b64_str)
            except Exception as e:
                return None, f"Invalid base64 payload: {str(e)}"

    if not raw_bytes:
        return None, "No image provided. Pass 'image' as base64 or multipart file."

    valid, err_msg, img = PayloadGuard.validate_image_bytes(raw_bytes)
    if not valid:
        return None, err_msg
    return img, None


def _image_to_base64_data_url(img: Image.Image, format: str = "JPEG", quality: int = 92) -> str:
    buf = io.BytesIO()
    if format.upper() == "PNG" or img.mode == "RGBA":
        img.save(buf, format="PNG")
        mime = "image/png"
    else:
        img.convert("RGB").save(buf, format="JPEG", quality=quality)
        mime = "image/jpeg"
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def handle_ai_get(handler: Any, path: str, query: Dict[str, list]) -> bool:
    """Dispatches GET /api/ai/* endpoints."""
    if path == "/api/ai/models":
        models = registry.list_models()
        handler.send_json({"status": "success", "count": len(models), "models": models})
        return True

    if path == "/api/ai/models/status":
        diag = run_system_diagnostics()
        handler.send_json({
            "status": diag["status"],
            "total_registered": diag["models_summary"]["total_registered"],
            "operational": diag["models_summary"]["operational"],
            "models": diag["models_summary"]["models"],
        })
        return True

    if path == "/api/ai/system/status":
        diag = run_system_diagnostics()
        handler.send_json(diag)
        return True

    return False


def handle_ai_post(handler: Any, path: str, body: Dict[str, Any]) -> bool:
    """Dispatches POST /api/ai/* endpoints."""
    start_time = time.time()

    # 1. Quality Analysis Endpoint
    if path == "/api/ai/analyze":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        analyzer = QualityAnalyzerAdapter()
        _, metrics = analyzer.execute(img)
        handler.send_json({"status": "completed", "analysis": metrics})
        return True

    # 2. Intelligent Auto-Enhance Pipeline
    if path == "/api/ai/auto-enhance":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        scale = int(body.get("scale", 4))
        allow_face = str(body.get("face_restore", "true")).lower() == "true"
        bokeh_r = int(body.get("bokeh_blur", 0))

        enhanced, steps, telem = orchestrator.run_auto_enhance(
            img, target_scale=scale, allow_face_restore=allow_face, bokeh_radius=bokeh_r
        )
        b64 = _image_to_base64_data_url(enhanced)
        handler.send_json({
            "status": "completed",
            "image": b64,
            "pipeline_steps": steps,
            "quality_metrics": telem["benchmarks"],
            "analysis": telem["analysis"],
            "duration_sec": telem["duration_sec"],
        })
        return True

    # 3. Super-Resolution
    if path == "/api/ai/super-resolution":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        scale = int(body.get("scale", 4))
        sr = SuperResolutionAdapter()
        enhanced, sr_metrics = sr.execute(img, scale=scale)
        b64 = _image_to_base64_data_url(enhanced)
        bench = BenchmarkMetrics.benchmark_run(img, enhanced, sr_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "scale": sr_metrics["requested_scale"],
            "quality_metrics": bench,
            "duration_sec": sr_metrics["duration_sec"],
        })
        return True

    # 4. Face Restoration
    if path == "/api/ai/face-restore":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        fidelity = float(body.get("fidelity_weight", 0.85))
        restorer = FaceRestorationAdapter()
        restored, r_metrics = restorer.execute(img, fidelity_weight=fidelity)
        b64 = _image_to_base64_data_url(restored)
        bench = BenchmarkMetrics.benchmark_run(img, restored, r_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": r_metrics["duration_sec"],
        })
        return True

    # 5. Denoise
    if path == "/api/ai/denoise":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        h_lum = float(body.get("h_luminance", 7.0))
        denoiser = ImageDenoiserAdapter()
        denoised, d_metrics = denoiser.execute(img, h_luminance=h_lum)
        b64 = _image_to_base64_data_url(denoised)
        bench = BenchmarkMetrics.benchmark_run(img, denoised, d_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": d_metrics["duration_sec"],
        })
        return True

    # 6. Deblur
    if path == "/api/ai/deblur":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        strength = float(body.get("strength", 1.0))
        deblurrer = MotionDeblurAdapter()
        deblurred, db_metrics = deblurrer.execute(img, strength=strength)
        b64 = _image_to_base64_data_url(deblurred)
        bench = BenchmarkMetrics.benchmark_run(img, deblurred, db_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": db_metrics["duration_sec"],
        })
        return True

    # 7. Low-Light
    if path == "/api/ai/lowlight":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        gamma = float(body.get("gamma", 1.35))
        lowlighter = LowLightAdapter()
        enhanced, ll_metrics = lowlighter.execute(img, gamma=gamma)
        b64 = _image_to_base64_data_url(enhanced)
        bench = BenchmarkMetrics.benchmark_run(img, enhanced, ll_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": ll_metrics["duration_sec"],
        })
        return True

    # 8. Background Removal
    if path == "/api/ai/background-remove":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        bg_rem = BackgroundRemoverAdapter()
        cutout, bg_metrics = bg_rem.execute(img)
        b64 = _image_to_base64_data_url(cutout, format="PNG")
        handler.send_json({
            "status": "completed",
            "image": b64,
            "format": "image/png",
            "duration_sec": bg_metrics["duration_sec"],
        })
        return True

    # 9. Optical Bokeh Blur
    if path == "/api/ai/bokeh":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        radius = int(body.get("radius", 15))
        bokeh_ad = BokehBlurAdapter()
        b_img, b_metrics = bokeh_ad.execute(img, radius=radius)
        b64 = _image_to_base64_data_url(b_img)
        bench = BenchmarkMetrics.benchmark_run(img, b_img, b_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": b_metrics["duration_sec"],
        })
        return True

    # 10. Colorize
    if path == "/api/ai/colorize":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        sat = float(body.get("saturation", 1.15))
        warm = float(body.get("warmth", 1.05))
        colorizer = PhotoColorizerAdapter()
        c_img, c_metrics = colorizer.execute(img, saturation=sat, warmth=warm)
        b64 = _image_to_base64_data_url(c_img)
        bench = BenchmarkMetrics.benchmark_run(img, c_img, c_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": c_metrics["duration_sec"],
        })
        return True

    # 11. Old Photo Restoration
    if path == "/api/ai/old-photo-restore":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        rem_scratches = str(body.get("remove_scratches", "true")).lower() == "true"
        restorer = OldPhotoRestorationAdapter()
        r_img, r_metrics = restorer.execute(img, remove_scratches=rem_scratches)
        b64 = _image_to_base64_data_url(r_img)
        bench = BenchmarkMetrics.benchmark_run(img, r_img, r_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": r_metrics["duration_sec"],
        })
        return True

    return False
