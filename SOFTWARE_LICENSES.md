# SOFTWARE LICENSES & OPEN-SOURCE ATTRIBUTION MATRIX
**Platform:** Adobe Studio Pro • SoundWave Infrastructure  
**Owner:** Sallu  
**Date:** November 26, 2026  
**Compliance Standard:** Open-Source Commercial Readiness & Research Isolation  

---

## 1. REPOSITORY LICENSE AUDIT TABLE

| Capability | Repository & Upstream Author | Source License | Weights License | Commercial Permission | Hardware Profile | Production Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Super-Resolution** | [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) (Xintao Wang) | BSD 3-Clause | BSD 3-Clause | **Permitted** | CPU + CUDA (RAM: ~50MB) | **ACTIVE_COMMERCIAL** |
| **Face Restoration** | [GFPGAN](https://github.com/TencentARC/GFPGAN) (Tencent ARC) | Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA (RAM: ~65MB) | **ACTIVE_COMMERCIAL** |
| **Face Quality & Codebook** | [CodeFormer](https://github.com/sczhou/CodeFormer) (S-Lab) | S-Lab License | Non-Commercial | **RESEARCH_ONLY** | CUDA Required | **ISOLATED_DEV** |
| **Image Restoration** | [SwinIR](https://github.com/JingyunLiang/SwinIR) (ETH Zürich) | Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |
| **Image Restoration Core** | [BasicSR](https://github.com/XPixelGroup/BasicSR) (XPixel Group)| Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |
| **Ultra Super-Resolution** | [SUPIR](https://github.com/Fanghua-Yu/SUPIR) (Fanghua Yu) | Apache 2.0 | Apache 2.0 | **Permitted** | GPU Only (16GB+ VRAM) | **EXTERNAL_GPU_ONLY** |
| **Deblur & Denoise** | [NAFNet](https://github.com/megvii-research/NAFNet) (Megvii) | Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |
| **Old Photo Restoration** | [Bringing-Old-Photos-Back-to-Life](https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life) (Microsoft)| MIT | Research Prior | **Restricted** | CPU + CUDA | **ACTIVE_HYBRID** |
| **High-Res Cutout** | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) (ZhengPeng) | MIT | MIT | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |
| **Zero-Shot Segmentation** | [SAM 2](https://github.com/facebookresearch/sam2) (Meta AI) | Apache 2.0 | Apache 2.0 | **Permitted** | GPU / Heavy CPU | **EXTERNAL_GPU_ONLY** |
| **Inpainting & Scratch Healing** | [LaMa](https://github.com/advimman/lama) (Samsung AI) | Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |
| **Deep Colorization** | [DDColor](https://github.com/piddnad/DDColor) (Dameng Xia) | Apache 2.0 | Apache 2.0 | **Permitted** | CPU + CUDA | **ACTIVE_COMMERCIAL** |

---

## 2. COMPLIANCE & SAFETY POLICIES

1. **Commercial Usage Guardrails:**
   - Any repository or pretrained checkpoint containing a "Non-Commercial" clause (such as CodeFormer default checkpoints) is strictly tagged `RESEARCH_ONLY`.
   - Production self-hosted endpoints default exclusively to BSD 3-Clause, Apache 2.0, and MIT licensed architectures.
2. **Attribution & Transparency:**
   - Reconstructed textures and neural approximations are never claimed as original camera evidence.
   - Quality metrics (PSNR, SSIM, Latency) reflect genuine calculations performed directly on the image arrays.
3. **Zero Untrusted Script Execution:**
   - No external `bash` or `curl | sh` scripts are executed. All model operations run through clean, inspectable Python code.
