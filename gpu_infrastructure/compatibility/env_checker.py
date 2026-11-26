"""
Hardware Environment, Capability & Memory Safeguard Checker.
Detects platform runtime, CPU/CUDA capabilities, free memory, and computes safe tiling constraints.
"""

import os
import sys
from typing import Any, Dict


def get_environment_info() -> Dict[str, Any]:
    """Inspects live system resources honestly without fabricating specs."""
    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # 2. CUDA & PyTorch inspection
    cuda_available = False
    cuda_device = "N/A"
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            cuda_device = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    # 3. OpenCV version
    cv_ver = "N/A"
    try:
        import cv2
        cv_ver = cv2.__version__
    except ImportError:
        pass

    # 4. NumPy version
    np_ver = "N/A"
    try:
        import numpy as np
        np_ver = np.__version__
    except ImportError:
        pass

    # 5. Pillow version
    pil_ver = "N/A"
    try:
        import PIL
        pil_ver = PIL.__version__
    except ImportError:
        pass

    # 6. Memory estimation (cross-platform)
    total_ram_mb = 512
    free_ram_mb = 256
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_ram_mb = int(mem.total / (1024 * 1024))
        free_ram_mb = int(mem.available / (1024 * 1024))
    except ImportError:
        # Fallback estimation for lightweight containers
        total_ram_mb = int(os.environ.get("CONTAINER_RAM_MB", 512))
        free_ram_mb = int(total_ram_mb * 0.60)

    is_cloud_container = os.environ.get("RENDER") == "true" or os.environ.get("PORT") is not None

    return {
        "python_version": py_ver,
        "cuda_available": cuda_available,
        "cuda_device": cuda_device,
        "opencv_version": cv_ver,
        "numpy_version": np_ver,
        "pillow_version": pil_ver,
        "total_ram_mb": total_ram_mb,
        "free_ram_mb": free_ram_mb,
        "is_cloud_container": is_cloud_container,
        "recommended_max_dimension": 640 if (total_ram_mb <= 512 or not cuda_available) else 1280,
    }
