# SoundWave Production GPU Architecture & Operations Guide

## 1. Executive Summary & Architecture Overview
This architecture establishes a provider-independent, horizontally scalable GPU inference infrastructure for deep image super-resolution (**Real-ESRGAN**) and blind face restoration (**GFPGAN**).

```
[ User Request ]
       │
       ▼
[ Security & Privacy Router ] ──(Personal Photo)──► [ Trusted GPU Workers Only ]
       │                                                 ├─ Primary: Self-Hosted (RTX 4090)
       │                                                 └─ Secondary: External Cloud (A10G)
       │
       └──(Public / Test + Consent)───────────────► [ Community Workers (Kalavai) ]
                                                         └─ Dev Fallback: HF ZeroGPU
```

---

## 2. Operational Cost Model

### A. Compute Infrastructure Options
| Tier | Hardware / Service | Hourly Cost | Monthly Cost (24/7) | Est. Latency / Photo | Cost per 1,000 Enhancements |
|---|---|---|---|---|---|
| **Self-Hosted Primary** | Dedicated RTX 4090 (24GB) | ~$0.05/hr (Power @ 350W) | ~$36.00/mo (Power only) | 0.8s - 1.4s | **$0.02** |
| **Secondary Cloud** | RunPod / Lambda (NVIDIA A10G) | $0.70/hr (On-Demand) | Auto-scales (Pay per min) | 1.1s - 1.8s | **$0.35** |
| **Enterprise Cloud** | AWS G5 / A100-SXM4 (80GB) | $2.50 - $3.60/hr | Fixed cluster reservation | 0.5s - 0.9s | **$0.80** |
| **Dev Fallback** | Hugging Face ZeroGPU | $0.00 (Free Tier) | Quota-capped (~300s/day) | 2.5s - 4.0s | **$0.00 (Rate Limited)** |
| **Community Pool** | Kalavai Decentralized P2P | Best-effort / volunteer | Variable token/credit model | 3.0s - 8.0s | **$0.00 (Test Only)** |

### B. Network & Storage Costs
- **No Persistent Cloud Storage Needed**: User images are processed in-memory (RAM buffer) and never stored in long-term S3 buckets, saving **$0.023/GB/month** storage and preventing privacy breaches.
- **Egress Bandwidth**: ~2.5 MB per 4K enhanced image. At AWS/Cloudflare standard rates (~$0.05/GB), bandwidth is **~$0.12 per 1,000 images**.

---

## 3. Licensing & Legal Compliance Matrix

| Component | Code License | Model Weights License | Commercial Deployment Status | Required Action |
|---|---|---|---|---|
| **Real-ESRGAN** | BSD 3-Clause | BSD 3-Clause | ✅ Fully Approved for Commercial Use | Retain copyright notice in software bundle. |
| **GFPGAN** | Apache 2.0 | Creative Commons BY-NC-SA 4.0 (FFHQ training data) | ⚠️ **Non-Commercial Restriction on default weights** | For commercial products, model must either be fine-tuned on commercial datasets or reviewed by IP legal counsel. |
| **Pillow / NumPy** | HPND / BSD-3 | N/A | ✅ Fully Approved | Permissive open-source standard. |
| **PyTorch / CUDA** | BSD-style / NVIDIA EULA | N/A | ✅ Approved | Standard server deployment terms. |

---

## 4. Security & Privacy Non-Negotiables

1. **Zero Public URLs**:
   - User photos are **never** hosted on public URLs or static web directories.
   - All image payloads are passed as in-memory bytes or authenticated ephemeral stream buffers.
2. **Air-Gapped Privacy Boundaries**:
   - Images tagged `JobPrivacy.PERSONAL` are **cryptographically and architecturally blocked** from community workers (Kalavai/P2P).
   - If only community workers are available, the router returns `503 GPU_UNAVAILABLE` rather than violating privacy.
3. **Explicit Contributor Consent**:
   - Community workers can only process `JobPrivacy.PUBLIC_TEST` images when `has_contributor_consent == True`.
4. **Memory Hygiene & Ephemeral Processing**:
   - Images are immediately dropped from RAM once sent to the client.
   - PyTorch CUDA memory is explicitly freed after every job:
     ```python
     torch.cuda.empty_cache()
     gc.collect()
     ```

---

## 5. External Service Dependencies & Failure Modes

1. **Kalavai P2P Pool**:
   - *Status*: Treated as an experimental, unverified community network.
   - *Failure Mode*: Worker churn, high packet loss, or node drop-off.
   - *Mitigation*: 45-second strict timeout, zero personal photo routing, and automatic failover.
2. **GPUStack**:
   - *Status*: Cluster manager for nodes.
   - *Failure Mode*: Does not natively bundle Real-ESRGAN or GFPGAN as ready-made REST services.
   - *Mitigation*: We maintain dedicated custom Python workers running on assigned GPUStack nodes.
3. **Hugging Face ZeroGPU**:
   - *Status*: Free-tier dev fallback.
   - *Failure Mode*: Hard 60-second burst limit and daily quota exhaustion.
   - *Mitigation*: Router tracks `daily_quota_used_seconds` and marks the worker `quota_exhausted` before failure occurs.
4. **Finite Capacity Policy (No False Promises)**:
   - The system **never** advertises "Unlimited Free Processing" or "100% Guaranteed GPU Availability".
   - When all workers are fully saturated, the system returns:
     ```json
     {
       "status": "gpu_unavailable",
       "code": 503,
       "message": "All GPU compute workers are currently busy. Capacity is finite; please retry in a few moments."
     }
     ```

---

## 6. Deployment Environments Matrix

- **`.env.local`**: Local development; CPU reference runner; mock VRAM telemetry.
- **`.env.private_cluster`**: Dedicated RTX 4090 / A100 nodes + GPUStack orchestration.
- **`.env.community`**: Kalavai P2P test pool with strict consent and public-test-only gating.
- **`.env.production`**: Primary A100 node with secondary Cloud A10G failover, IP rate-limiting, and strict 503 capacity gates.
