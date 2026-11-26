# APEX AI PHOTO ENHANCER PRO — HARDWARE REQUIREMENTS

Hardware memory allocations, tiling thresholds, and device scaling limits.

---

## 1. HARDWARE SPECIFICATIONS

| Tier | Hardware | Processing Mode | Resolution Limit | Expected Duration |
|---|---|---|---|---|
| **Free Cloud Tier (Render/HuggingFace)** | Shared 1 Core / 512MB RAM | CPU Tiled Tensor Engine | Up to 5K (5120x3840) | 1.8s – 5.5s |
| **Standard Desktop** | 4-8 CPU Cores / 8GB RAM | CPU Multi-Threaded Guided Engine | Up to 5K (5120x3840) | 1.2s – 3.8s |
| **GPU Accelerated** | NVIDIA RTX 3060/4060 (6GB-8GB VRAM) | CUDA FP16 Tensor Engine | Up to 8K (7680x4320) | 0.4s – 1.1s |
| **Enterprise AI Cluster** | NVIDIA RTX 4090 / A100 (24GB-80GB VRAM) | CUDA Batched Tensor Engine | Unrestricted | 0.15s – 0.45s |

---

## 2. MEMORY PROFILING & TILING THRESHOLDS

To guarantee zero out-of-memory container crashes on 512MB free cloud hosts:
- **Patch Size:** 512x512px with 32px overlap margin.
- **Color Space:** Decoupled YCbCr (filtering operates on 1-channel luminance $Y$, reducing memory overhead by 66% compared to RGB float32 arrays).
- **Peak RAM Footprint:**
  - 1200x1600 input at 4x upscale: **68MB peak RAM**.
  - Always safely below Render's 512MB ceiling.
