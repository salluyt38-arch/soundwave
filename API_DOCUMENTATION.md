# APEX AI PHOTO ENHANCER PRO — REST API SPECIFICATION

Comprehensive reference for all REST endpoints provided by the APEX AI Backend.

Base URL: `http://localhost:5000/api` (or `https://your-domain.com/api`)

---

## 1. ENDPOINTS SUMMARY

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Multipart image upload returning temporary `file_id` and dimensions |
| `POST` | `/api/enhance` | Master one-click AI restoration (Real-ESRGAN + GFPGAN/CodeFormer) |
| `POST` | `/api/face-restore` | Dedicated facial reconstruction with fidelity weight control |
| `POST` | `/api/upscale` | Super-resolution image upscaling (2x, 4x, 8x) |
| `POST` | `/api/old-photo-restore` | Vintage photo scratch repair, tear removal, and contrast expansion |
| `POST` | `/api/colorize` | Black & white photo colorization |
| `POST` | `/api/denoise` | Sensor grain and ISO noise reduction |
| `POST` | `/api/inpaint` | Object removal and inpainting from user-drawn mask |
| `GET` | `/api/jobs/{job_id}` | Polls real-time job status, progress, and quality metrics |
| `POST` | `/api/jobs/{job_id}/cancel` | Cancels an active or queued job |
| `GET` | `/api/download/{job_id}` | Streams the completed high-resolution output file |
| `GET` | `/api/download/preview/{file_id}` | Streams the uploaded original file for browser preview |
| `GET` | `/api/models` | Returns model catalog, licenses, and hardware acceleration status |
| `GET` | `/api/health` | Hardware capability introspection, VRAM, and health check |
| `GET` | `/api/history` | Lists recently processed enhancement jobs |

---

## 2. DETAILED ENDPOINT SCHEMAS

### POST `/api/enhance`
Executes intelligent master enhancement.

**Request Payload (JSON):**
```json
{
  "image": "data:image/jpeg;base64,...",
  "scale": 4,
  "face_restore": true,
  "face_strength": 0.85,
  "denoise_strength": 0.5,
  "color_correct": true,
  "is_async": false
}
```

**Success Response (HTTP 200):**
```json
{
  "job_id": "apex_job_1795673842898_a4f912",
  "status": "completed",
  "progress_percent": 100,
  "task_type": "auto_enhance",
  "models_used": ["swinir_denoise", "gfpgan_v1.4", "codeformer_fidelity", "real_esrgan_4x"],
  "input_resolution": "1200x1600",
  "output_resolution": "4800x6400",
  "created_at": 1795673842.898,
  "completed_at": 1795673845.210,
  "duration_sec": 2.31,
  "quality_metrics": {
    "psnr_db": 34.82,
    "ssim": 0.9825,
    "blur_score": 580.4,
    "white_clipping_ratio": 0.001,
    "black_clipping_ratio": 0.002,
    "exposure_safe": true,
    "quality_grade": "EXCELLENT",
    "inference_duration_sec": 2.31,
    "input_resolution": "1200x1600",
    "output_resolution": "4800x6400",
    "scale": "4x"
  },
  "result_url": "/api/download/apex_job_1795673842898_a4f912",
  "image": "data:image/jpeg;base64,..."
}
```

---

### POST `/api/face-restore`
Executes facial reconstruction.

**Request Payload (JSON):**
```json
{
  "image": "data:image/jpeg;base64,...",
  "model_name": "codeformer",
  "fidelity": 0.85,
  "eye_enhancement": true,
  "skin_polish": true,
  "lip_enhancement": true
}
```

---

### POST `/api/old-photo-restore`
Removes scratches and recovers vintage dynamic range.

**Request Payload (JSON):**
```json
{
  "image": "data:image/jpeg;base64,...",
  "remove_scratches": true,
  "colorize": true,
  "face_restore": true,
  "contrast_recovery": true
}
```

---

### GET `/api/health`
Introspects host hardware, CUDA availability, free memory, and active workers.

**Success Response (HTTP 200):**
```json
{
  "status": "healthy",
  "service": "APEX AI Photo Enhancer Pro",
  "platform_version": "2.4.0",
  "owner": "Sallu",
  "device": "cpu",
  "cuda_available": false,
  "active_workers": 1,
  "loaded_models": ["real-esrgan", "gfpgan", "codeformer", "swinir", "lama", "colorization"],
  "memory_free_mb": 4210,
  "timestamp": 1795673845.0
}
```
