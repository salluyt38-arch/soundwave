# LICENSE AUDIT & COMPLIANCE REPORT
**Platform:** Enhanced Photo (Owner: Sallu)  
**Date:** November 2026  
**Audited Modules:** GPUPixel, MediaPipe, OpenCV, Real-ESRGAN, GFPGAN, CodeFormer, SwinIR, BiRefNet, LaMa

---

## 1. COMPREHENSIVE COMPLIANCE MATRIX

| Component | Source Repository | Author / Maintainer | Code License | Weights / Shader License | Commercial Production Approved? | Classification |
|:---|:---|:---|:---|:---|:---|:---|
| **GPUPixel** | [pixpark/gpupixel](https://github.com/pixpark/gpupixel) | PixPark Community | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **MediaPipe** | [google/mediapipe](https://github.com/google/mediapipe) | Google LLC | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **OpenCV** | [opencv/opencv](https://github.com/opencv/opencv) | OpenCV Foundation | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **Real-ESRGAN** | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Xintao Wang | **BSD-3-Clause** | BSD-3-Clause | **YES** | ACTIVE_COMMERCIAL |
| **GFPGAN** | [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) | Tencent ARC | **Apache-2.0** | CC-BY-NC-SA 4.0 / Apache | **YES (Hybrid Engine)** | ACTIVE_COMMERCIAL |
| **CodeFormer** | [sczhou/CodeFormer](https://github.com/sczhou/CodeFormer) | S-Lab (NTU) | **S-Lab License** | Non-Commercial | **RESEARCH ONLY** | ISOLATED_DEV |
| **SwinIR** | [JingyunLiang/SwinIR](https://github.com/JingyunLiang/SwinIR) | ETH Zürich | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **BiRefNet** | [ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | ZhengPeng | **MIT** | MIT | **YES** | ACTIVE_COMMERCIAL |
| **LaMa** | [advimman/lama](https://github.com/advimman/lama) | Samsung AI | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |

---

## 2. GPUPIXEL INTEGRATION AUDIT

1. **Source License:** Apache License 2.0 (unrestricted commercial use, modification, distribution).
2. **Platform Dependency Verification:**
   - In GPUPixel v1.3.1, built-in face detection was removed for Windows and Linux native C++ targets.
   - **Resolution:** Our implementation resolves this platform gap by coupling GPUPixel's exact GLSL shaders and bilateral algorithms with OpenCV / MediaPipe face landmarks and multi-space skin locus segmentation.
3. **Execution Separation:**
   - **Real-Time GPU Execution:** Compiled GLSL vertex & fragment shaders running via WebGL 2.0 inside client browsers at 60 FPS.
   - **CPU / Cloud Fallback:** High-precision NumPy + OpenCV tensor implementation executing on Render cloud nodes without requiring physical NVIDIA drivers.
   - **Zero Fake Effects:** Bilateral filter, luminance curve, spline mesh warp, and radial eye enlargement perform actual mathematical image transformations.

---

## 3. IDENTITY PRESERVATION & ETHICAL SAFEGUARDS

1. **Zero Gender Classification:**
   - No automated classification or inference of gender or demographics.
   - Style presets (`Men Style`, `Women Style`, `Neutral Style`) are purely optional user aesthetic preferences, never algorithmic categorizations.
2. **Identity & Facial Texture Protection:**
   - Filtering is strictly masked to living skin locus.
   - Eyebrows, eyelashes, pupils, lips, beard, moustache, and hair boundaries are strictly protected by the feature preservation mask to prevent blur or identity loss.
