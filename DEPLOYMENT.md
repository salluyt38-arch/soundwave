# APEX AI PHOTO ENHANCER PRO — DEPLOYMENT GUIDE

Production deployment instructions for Docker, Render, self-hosted Linux servers, and cloud clusters.

---

## 1. RENDER CLOUD DEPLOYMENT (DOCKER / NATIVE)

The repository includes a ready-to-deploy `Dockerfile` and `render.yaml`.

### Render Environment Configuration:
Set the following environment variables in Render Dashboard:
- `PORT`: `5000`
- `PYTHONUNBUFFERED`: `1`
- `PRIMARY_GPU_MODEL`: `Auto-Detect`

Render automatically pulls from `origin/main` and runs the container. The health check endpoint is at `GET /api/health`.

---

## 2. DOCKER DEPLOYMENT

Build and run the container locally or on any cloud VPS (AWS, GCP, DigitalOcean, Hetzner):

```bash
# Build Docker image
docker build -t apex-ai-enhancer:latest .

# Run container (CPU mode)
docker run -d -p 5000:5000 --name apex-ai apex-ai-enhancer:latest

# Run container with NVIDIA GPU acceleration (requires nvidia-container-toolkit)
docker run -d --gpus all -p 5000:5000 --name apex-ai apex-ai-enhancer:latest
```

---

## 3. FREE-FIRST ARCHITECTURE GUARANTEE

1. **Zero Mandatory Paid APIs:**
   The entire APEX AI engine runs self-hosted models without calling external metered APIs (OpenAI, Replicate, Stability, etc.).
2. **Horizontal Scaling:**
   Worker adapters process 1 job per core independently. Memory tiling limits peak RAM consumption to <95MB per thread.
3. **Automatic Ephemeral Cleanup:**
   Uploaded and processed artifacts expire and are deleted from disk automatically after 10 minutes (`ARTIFACT_EXPIRY_SECONDS = 600`), preventing disk saturation.
