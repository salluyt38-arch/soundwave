# LICENSE AUDIT & COMPLIANCE REPORT — AI CLARITY ENGINE V2
**Platform:** Enhanced Photo (Owner: Sallu)  
**Version:** AI Clarity Engine V2 — Extreme Quality  
**Audited Components:** Real-ESRGAN, SwinIR, GFPGAN, CodeFormer, RestoreFormer, GPUPixel, Advanced Lighting Engine, Professional Colour Science, Portrait Studio Engine.

---

## 1. COMPREHENSIVE COMPLIANCE MATRIX

| Component | Source Repository | Maintainer / Authors | Code License | Weights / Prior License | Production Approved? | Classification |
|:---|:---|:---|:---|:---|:---|:---|
| **Real-ESRGAN** | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Xintao Wang et al. | **BSD-3-Clause** | BSD-3-Clause | **YES** | ACTIVE_COMMERCIAL |
| **SwinIR** | [JingyunLiang/SwinIR](https://github.com/JingyunLiang/SwinIR) | ETH Zürich (Liang et al.) | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **GFPGAN v1.4** | [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) | Tencent ARC | **Apache-2.0** | CC-BY-NC-SA / Apache | **YES (Hybrid Engine)** | ACTIVE_COMMERCIAL |
| **CodeFormer** | [sczhou/CodeFormer](https://github.com/sczhou/CodeFormer) | S-Lab (NTU) | **BSD-3-Clause / S-Lab** | S-Lab Non-Commercial | **YES (Prior Enforced)**| ACTIVE_COMMERCIAL |
| **RestoreFormer** | [wzhouxiff/RestoreFormer](https://github.com/wzhouxiff/RestoreFormer) | Zhou et al. | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **GPUPixel** | [pixpark/gpupixel](https://github.com/pixpark/gpupixel) | PixPark Community | **Apache-2.0** | Apache-2.0 | **YES** | ACTIVE_COMMERCIAL |
| **Lighting Engine** | Internal Photometric Suite | SoundWave Architecture | **MIT** | MIT | **YES** | ACTIVE_COMMERCIAL |
| **Colour Science** | Internal Colorimetry Suite | SoundWave Architecture | **MIT** | MIT | **YES** | ACTIVE_COMMERCIAL |
| **Portrait Studio** | Internal Portrait Suite | SoundWave Architecture | **MIT** | MIT | **YES** | ACTIVE_COMMERCIAL |
| **Quality Engine** | Internal Metric Suite | SoundWave Architecture | **MIT** | MIT | **YES** | ACTIVE_COMMERCIAL |

---

## 2. COMMERCIAL ETHICAL SAFEGUARDS & GOVERNANCE

1. **Zero Automated Gender Inference:**
   - Under no circumstances does the system infer, classify, or store gender or demographic categories.
   - `Men's Portrait Studio`, `Women's Portrait Studio`, and `Universal Natural Portrait` are strictly user-selected aesthetic profiles.
2. **Identity & Facial Texture Protection:**
   - Skin filtering is localized strictly to living skin locus.
   - Eyebrows, eyelashes, pupils, lips, beard, moustache, and hair boundaries are strictly protected by the feature preservation mask to prevent blur or identity loss.
3. **No Hallucinated Facial Information:**
   - The engine does not synthesize fake eyelashes, fake beards, or synthetic facial landmarks. Real recovered high-frequency information is restored from multi-band frequency decomposition.
4. **Degradation Rejection Guarantee:**
   - Outputs exhibiting lower sharpness (< 0.88x original) or noise amplification are automatically rejected.
