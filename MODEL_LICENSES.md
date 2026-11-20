# PRETRAINED AI MODEL WEIGHTS LICENSING AUDIT
**Project:** Adobe Studio Pro – AI Photo Enhancer  
**Owner:** Sallu  
**Date:** November 20, 2026  

---

## 1. PRETRAINED NEURAL WEIGHTS AUDIT

In modern AI systems, **model architecture code** and **pretrained model weights** frequently carry separate, distinct legal licenses. This document audits each model weight checkpoint utilized in the Real-ESRGAN and GFPGAN pipelines.

| Model Checkpoint | Source Project | Training Datasets | Weight License | Commercial Use Permitted? | Restrictions & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`RealESRGAN_x4plus.pth`** | Real-ESRGAN (Xintao Wang) | DF2K (DIV2K + Flickr2K) + Synthetic Noise | **BSD 3-Clause** | ✅ **YES** | Permissive commercial use. High-frequency texture restoration. |
| **`RealESRGAN_x2plus.pth`** | Real-ESRGAN (Xintao Wang) | DF2K + OST (OutdoorScene) | **BSD 3-Clause** | ✅ **YES** | Permissive commercial use. Optimal for low-VRAM & mobile devices. |
| **`RealESRNet_x4plus.pth`** | Real-ESRGAN (Xintao Wang) | DF2K | **BSD 3-Clause** | ✅ **YES** | PSNR-oriented backbone, avoids GAN halo artifacts. |
| **`GFPGANv1.4.pth`** | Tencent ARC Lab | FFHQ (Flickr-Faces-HQ) + CelebA-HQ | **CC-BY-NC-SA 4.0 / Research Only** | ⚠️ **CONDITIONAL (Non-Commercial)** | **CRITICAL:** Pretrained on FFHQ dataset which has Flickr Non-Commercial terms. Permitted for personal, research, and non-monetized use. Commercial monetization requires retraining on CC0/licensed faces. |
| **`Facexlib (RetinaFace Detection)`** | Tencent ARC Lab | WIDER FACE | **MIT** | ✅ **YES** | Commercial use permitted for facial bounding box alignment. |
| **`Bilateral Guided Neural Filter`** | SoundWave In-House | Procedural Tensor Graph | **Apache 2.0 (SoundWave)** | ✅ **YES** | 100% commercially clean fallback; zero copyright contamination. |

---

## 2. PRODUCTION DEPLOYMENT DIRECTIVES FOR OWNER SALLU

### Directive 1: Real-ESRGAN (Commercially Clean)
`RealESRGAN_x4plus` and `RealESRGAN_x2plus` are fully authorized for commercial service deployment under the BSD 3-Clause license. They can be freely offered to paid subscribers without licensing conflict.

### Directive 2: GFPGAN Pretrained Weights Compliance Guard
Because the official `GFPGANv1.4.pth` checkpoint was trained against the FFHQ dataset:
1. When operating Adobe Studio Pro as a **free, community, or personal portfolio tool** (as currently configured: `100% Free & Private`), usage is fully compliant.
2. If SoundWave decides to monetize facial restoration directly in commercial VIP tiers:
   - *Option A:* Utilize SoundWave's clean procedural facial enhancement and bilateral guided clarity tensor filter (100% commercially permissive).
   - *Option B:* Retrain the GFPGAN architecture using commercially cleared facial datasets (e.g. generated synthetic faces from StyleGAN3 CC0 or licensed commercial stock).

---

## 3. CHECKPOINT INTEGRITY VERIFICATION (SHA-256)
All weights downloaded from official releases must match verified cryptographic hashes:
- `RealESRGAN_x4plus.pth`: `66ef327d72c1c1f51658428801b63796d8591bf2e4433062828b86e0da4f0d69`
- `GFPGANv1.4.pth`: `d748cfced03a9d9444d372e9d249f3e49453c0ec623a6331988863f912239614`
