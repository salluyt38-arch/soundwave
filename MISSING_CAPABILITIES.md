# MISSING CAPABILITIES & ARCHITECTURAL GAPS: ADOBE STUDIO PRO
**Owner:** Sallu  
**Date:** November 26, 2026  
**Evaluation Scope:** Complete Audit against Phase 5 & Phase 10 Requirements  

---

## 1. IDENTIFIED MISSING AI CAPABILITIES (PHASE 5)

| Required Capability | Current Implementation Status | Gap Description & Target Architecture |
| :--- | :--- | :--- |
| **1. AI Background Removal** | `PARTIALLY_IMPLEMENTED` | Needs high-precision neural foreground segmentation (BiRefNet / RMBG style alpha matte) that preserves fine hair strands and transparent fabrics. |
| **2. Motion Deblurring** | `NOT_IMPLEMENTED` | Camera shake / motion blur removal currently relies on unsharp masking; needs directional Wiener deblurring & NAFNet-inspired kernel restoration. |
| **3. Low-Light Recovery** | `PARTIALLY_IMPLEMENTED` | Basic gamma and brightness adjustment exists; needs Retinex / Zero-DCE illuminance decomposition to reveal dark shadow details without amplifying noise. |
| **4. AI Noise Removal (Denoising)**| `PARTIALLY_IMPLEMENTED` | Basic bilateral filter exists; needs Non-Local Means (NLM) / multi-scale wavelet denoising for high-ISO sensor noise. |
| **5. AI Image Quality Analyzer** | `PARTIALLY_IMPLEMENTED` | Basic PSNR/SSIM calculation exists; needs pre-processing quality classification (blur score, noise score, low-light score, face count) to drive auto-enhancement. |
| **6. JPEG Artifact Removal** | `PARTIALLY_IMPLEMENTED` | Standard deblocking filter missing; needs 8x8 DCT grid boundary de-ringing and de-blocking. |
| **7. Subject Isolation & Depth Map**| `PARTIALLY_IMPLEMENTED` | Radial ellipse mask currently used; needs monocular depth gradient approximation (MiDaS inspired) for realistic variable depth-of-field blur. |

---

## 2. MISSING API ENDPOINTS (PHASE 10)
The following standardized REST endpoints requested in Phase 10 are currently missing or need unification:
- `POST /api/ai/analyze` (Automatic problem classification and quality metric extraction)
- `POST /api/ai/auto-enhance` (Intelligent orchestrator selecting and executing optimal pipeline)
- `POST /api/ai/face-restore` (Dedicated facial reconstruction with fidelity control)
- `POST /api/ai/super-resolution` (Dedicated 2x, 4x, 8x, 500x upscaling endpoint)
- `POST /api/ai/denoise` (Dedicated multi-scale sensor noise reduction)
- `POST /api/ai/deblur` (Dedicated camera motion & lens defocus deblurring)
- `POST /api/ai/colorize` (Dedicated monochrome photo colorization)
- `POST /api/ai/background-remove` (Dedicated transparent PNG foreground cutout)
- `POST /api/ai/bokeh` (Dedicated optical depth blur with subject isolation)
- `POST /api/ai/old-photo-restore` (Dedicated scratch, tear, and defect removal)
- `GET /api/ai/models` (Catalog of registered models and operational specifications)
- `GET /api/ai/models/status` (Health check and availability of all model adapters)
- `GET /api/ai/system/status` (Telemetry on CPU, RAM, and GPU status)

---

## 3. MISSING ARCHITECTURAL COMPONENTS (PHASE 4)
- `gpu_infrastructure/model_registry/`: Needs standardized metadata records for every capability adapter.
- `gpu_infrastructure/model_adapters/`: Needs independent, modular adapter classes for each capability with unified `execute(img, **kwargs)` interfaces.
- `gpu_infrastructure/benchmarking/`: Needs a formal benchmark runner evaluating real images against PSNR, SSIM, execution time, and peak memory.
- `gpu_infrastructure/security/`: Needs strict MIME-type sniffing, dimension bounds, and payload sanitization.
- `gpu_infrastructure/diagnostics/`: Needs automated self-test scripts verifying all adapters upon startup.
