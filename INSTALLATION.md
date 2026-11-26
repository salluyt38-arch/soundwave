# APEX AI PHOTO ENHANCER PRO — INSTALLATION GUIDE

Step-by-step setup instructions for Windows and Linux environments.

---

## 1. PREREQUISITES

- **Operating System:** Windows 10/11 or Ubuntu 20.04/22.04 LTS
- **Python:** 3.10, 3.11, or 3.12 (64-bit)
- **RAM:** 4GB minimum (8GB recommended)
- **Optional GPU:** NVIDIA GPU with CUDA 11.8 or 12.x for accelerated inference. (Runs automatically on CPU if no GPU is available).

---

## 2. WINDOWS SETUP

### Step 1: Open PowerShell or Command Prompt
Navigate to the project root directory:
```powershell
cd C:\path\to\soundwave
```

### Step 2: Install Core Dependencies
Install the required packages:
```powershell
python -m pip install -r requirements.txt
python -m pip install opencv-python-headless fastapi uvicorn pydantic
```

*(Optional for CUDA GPU acceleration)*:
```powershell
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 3: Run the Server
You can launch either the FastAPI dedicated application or the multi-app SoundWave server:

**Option A — Launch Dedicated APEX FastAPI Server:**
```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 5000 --reload
```

**Option B — Launch Unified Multi-App Server:**
```powershell
python server.py
```

### Step 4: Open in Web Browser
- **APEX AI Photo Enhancer Pro:** `http://localhost:5000/apex.html`
- **Adobe Studio Pro:** `http://localhost:5000/photostudio.html`
- **Interactive Swagger API Docs:** `http://localhost:5000/docs`

---

## 3. LINUX (UBUNTU / DEBIAN) SETUP

```bash
# Update system
sudo apt-get update && sudo apt-get install -y ffmpeg libsm6 libxext6

# Install virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install opencv-python-headless fastapi uvicorn pydantic

# Run server
uvicorn backend.app.main:app --host 0.0.0.0 --port 5000
```
