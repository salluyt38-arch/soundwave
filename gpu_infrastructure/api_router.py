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
    JpegDeblockAdapter,
    SmartCompressorAdapter,
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


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively converts NumPy scalars, arrays, sets, and non-primitive types into pure Python types."""
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    elif hasattr(obj, "tolist"):
        return obj.tolist()
    elif isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    return str(obj)


def _send_json(handler: Any, data: Any, status: int = 200) -> None:
    sanitized = _sanitize_for_json(data)
    handler.send_json(sanitized, status=status)


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

    if path == "/api/ai/beauty/shaders":
        from .beauty import GPUPixelEngine
        handler.send_json({"status": "success", "shaders": GPUPixelEngine.get_webgl_shaders()})
        return True

    return False


def handle_ai_post(handler: Any, path: str, body: Dict[str, Any]) -> bool:
    """Dispatches POST /api/ai/* endpoints."""
    start_time = time.time()

    # 0A. GPUPixel Face Analysis Endpoint
    if path in ("/api/ai/face/analyze", "/api/face/analyze"):
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        from .beauty import FaceAnalyzer
        analyzer = FaceAnalyzer()
        res = analyzer.analyze(img)
        handler.send_json({
            "status": "completed",
            "analysis": res.to_dict(),
            "duration_sec": round(time.time() - start_time, 3)
        })
        return True

    # 0B. GPUPixel Beauty & Intelligent Face-Aware Filter Endpoint
    if path in ("/api/ai/beauty/filter", "/api/beauty/filter"):
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True

        from .beauty import FaceAnalyzer, GPUPixelEngine, IntelligentFilterEngine, PortraitFilterType, StylePreset

        # 1. Face & Lighting Analysis
        analyzer = FaceAnalyzer()
        analysis = analyzer.analyze(img)

        # 2. Extract Beauty Slider Params
        smooth_val = int(body.get("smooth", 0))
        whiten_val = int(body.get("whiten", 0))
        slimming_val = int(body.get("slimming", 0))
        eye_val = int(body.get("eye_enlarge", 0))
        tone_val = int(body.get("tone_balance", 0))

        # 3. Apply GPUPixel Beauty Effects
        gpu_engine = GPUPixelEngine()
        beauty_img, beauty_metrics = gpu_engine.apply_beauty_effects(
            img, analysis,
            smooth_intensity=smooth_val,
            whiten_intensity=whiten_val,
            face_slimming=slimming_val,
            eye_enlarging=eye_val,
            tone_balance=tone_val
        )

        # 4. Extract Filter & Style Preset Params
        filter_str = str(body.get("filter", "")).strip().lower()
        style_str = str(body.get("style", "neutral")).strip().lower()
        intensity = int(body.get("intensity", 100))

        final_img = beauty_img
        filter_metrics = {}

        if filter_str:
            try:
                ft = PortraitFilterType(filter_str)
            except ValueError:
                ft = PortraitFilterType.NATURAL_SKIN

            try:
                sp = StylePreset(style_str)
            except ValueError:
                sp = StylePreset.NEUTRAL

            filt_engine = IntelligentFilterEngine()
            final_img, filter_metrics = filt_engine.apply_filter(
                beauty_img, analysis, filter_type=ft, style_preset=sp, intensity=intensity
            )

        fmt = str(body.get("format", "JPEG")).upper()
        b64 = _image_to_base64_data_url(final_img, format=fmt)
        handler.send_json({
            "status": "completed",
            "image": b64,
            "beauty_metrics": beauty_metrics,
            "filter_metrics": filter_metrics,
            "analysis": analysis.to_dict(),
            "duration_sec": round(time.time() - start_time, 3)
        })
        return True

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

    # 2. Intelligent Auto-Enhance Pipeline (Autonomous Backend Master)
    if path in ("/api/ai/auto-enhance", "/api/auto-enhance"):
        img, err = _extract_image_payload(body)
        if err:
            _send_json(handler, {"error": err, "status": "invalid_payload"}, status=400)
            return True
        scale = int(body.get("scale", 2))
        allow_face = str(body.get("face_restore", "true")).lower() == "true"
        bokeh_r = int(body.get("bokeh_blur", 0))
        allow_beauty = str(body.get("beauty_pass", "true")).lower() == "true"
        style_preset = str(body.get("style", "neutral")).lower()

        enhanced, steps, telem = orchestrator.run_auto_enhance(
            img,
            target_scale=scale,
            allow_face_restore=allow_face,
            bokeh_radius=bokeh_r,
            allow_beauty=allow_beauty,
            style_preset=style_preset,
        )
        b64 = _image_to_base64_data_url(enhanced)
        _send_json(handler, {
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

    # 12. JPEG Artifact Deblock
    if path == "/api/ai/deblock":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        strength = float(body.get("strength", 1.0))
        deblocker = JpegDeblockAdapter()
        d_img, d_metrics = deblocker.execute(img, strength=strength)
        b64 = _image_to_base64_data_url(d_img)
        bench = BenchmarkMetrics.benchmark_run(img, d_img, d_metrics["duration_sec"])
        handler.send_json({
            "status": "completed",
            "image": b64,
            "quality_metrics": bench,
            "duration_sec": d_metrics["duration_sec"],
        })
        return True

    # 13. Smart Image Compression
    if path == "/api/ai/compress":
        img, err = _extract_image_payload(body)
        if err:
            handler.send_json({"error": err, "status": "invalid_payload"}, status=400)
            return True
        quality = int(body.get("quality", 82))
        fmt = str(body.get("format", "WEBP")).upper()
        compressor = SmartCompressorAdapter()
        c_img, c_metrics = compressor.execute(img, target_quality=quality, format=fmt)
        b64 = _image_to_base64_data_url(c_img, format=fmt)
        handler.send_json({
            "status": "completed",
            "image": b64,
            "metrics": c_metrics,
            "duration_sec": c_metrics["duration_sec"],
        })
        return True

    # 14. Batch Photo Enhancement
    if path == "/api/ai/batch-enhance":
        images_list = body.get("images", [])
        if not images_list or not isinstance(images_list, list):
            handler.send_json({"error": "Pass 'images' as a list of base64 strings.", "status": "invalid_payload"}, status=400)
            return True

        # Limit batch to 8 items to protect server memory
        max_batch = 8
        batch_slice = images_list[:max_batch]
        scale = int(body.get("scale", 2))
        results = []

        for idx, item in enumerate(batch_slice):
            sub_body = {"image": item}
            sub_img, sub_err = _extract_image_payload(sub_body)
            if sub_err or not sub_img:
                results.append({"index": idx, "status": "failed", "error": sub_err or "Invalid image"})
                continue
            enhanced, steps, telem = orchestrator.run_auto_enhance(sub_img, target_scale=scale, allow_face_restore=True)
            b64_out = _image_to_base64_data_url(enhanced)
            results.append({
                "index": idx,
                "status": "completed",
                "image": b64_out,
                "pipeline_steps": steps,
                "psnr_db": telem["benchmarks"]["psnr_db"],
            })

        handler.send_json({
            "status": "completed",
            "total_submitted": len(images_list),
            "processed_count": len(results),
            "results": results,
            "duration_sec": round(time.time() - start_time, 2),
        })
        return True

    return False
