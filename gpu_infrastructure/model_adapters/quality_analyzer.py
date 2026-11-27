"""
AI Image Quality Analyzer & Pre-Inference Problem Classifier Adapter.
Inspects blur, noise, exposure, and facial presence to classify input defects.
"""

import time
from typing import Any, Dict, List, Tuple
from PIL import Image

try:
    import cv2
    import numpy as np
    CV_OK = True
except ImportError:
    CV_OK = False

from .base_adapter import BaseCapabilityAdapter


class QualityAnalyzerAdapter(BaseCapabilityAdapter):
    """Analyzes image defects and outputs diagnostic telemetry."""

    def __init__(self):
        super().__init__(
            model_id="iqa_quality_analyzer",
            name="Pre-Inference Image Quality & Problem Classifier",
            category="Quality Assessment",
        )
        self.face_cascade = None
        if CV_OK:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                self.face_cascade = None

    def execute(self, img: Image.Image, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        start_time = time.time()
        w, h = img.size

        blur_score = 0.0
        noise_score = 0.0
        mean_brightness = 128.0
        contrast_score = 50.0
        faces_detected: List[Tuple[int, int, int, int]] = []
        is_low_light = False
        is_blurry = False
        is_noisy = False
        is_monochrome = False

        if CV_OK:
            arr = np.array(img.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

            # 1. Blur Detection (Variance of Laplacian)
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            blur_score = round(laplacian_var, 2)
            is_blurry = bool(blur_score < 120.0)

            # 2. Exposure & Low-Light
            mean_brightness = round(float(np.mean(gray)), 2)
            contrast_score = round(float(np.std(gray)), 2)
            is_low_light = bool(mean_brightness < 75.0 or (mean_brightness < 90.0 and contrast_score < 35.0))

            # 3. High-ISO Noise Estimation
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_arr = cv2.absdiff(gray, blurred)
            noise_score = round(float(np.mean(noise_arr)), 2)
            is_noisy = bool(noise_score > 8.5)

            # 4. Color vs Monochrome Detection
            diff_rg = float(np.mean(np.abs(arr[:, :, 0].astype(float) - arr[:, :, 1].astype(float))))
            diff_gb = float(np.mean(np.abs(arr[:, :, 1].astype(float) - arr[:, :, 2].astype(float))))
            is_monochrome = bool((diff_rg < 3.5) and (diff_gb < 3.5))

            # 5. Face Detection
            if self.face_cascade and not self.face_cascade.empty():
                # Downsample large images for fast cascade detection
                scale = max(1.0, max(w, h) / 640.0)
                small_w = int(w / scale)
                small_h = int(h / scale)
                small_gray = cv2.resize(gray, (small_w, small_h))
                rects = self.face_cascade.detectMultiScale(
                    small_gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
                )
                for (x, y, fw, fh) in rects:
                    rx0 = int(x * scale)
                    ry0 = int(y * scale)
                    rw = int(fw * scale)
                    rh = int(fh * scale)
                    faces_detected.append((rx0, ry0, rw, rh))

        # Problem classification tags
        detected_problems = []
        if is_blurry:
            detected_problems.append("defocus_or_motion_blur")
        if is_low_light:
            detected_problems.append("underexposed_shadows")
        if is_noisy:
            detected_problems.append("high_iso_sensor_noise")
        if is_monochrome:
            detected_problems.append("monochrome_photo")
        if len(faces_detected) > 0:
            detected_problems.append(f"faces_present_{len(faces_detected)}")

        duration = round(time.time() - start_time, 3)

        metrics = {
            "resolution": f"{w}x{h}",
            "blur_score": float(blur_score),
            "is_blurry": bool(is_blurry),
            "mean_brightness": float(mean_brightness),
            "contrast_score": float(contrast_score),
            "is_low_light": bool(is_low_light),
            "noise_score": float(noise_score),
            "is_noisy": bool(is_noisy),
            "is_monochrome": bool(is_monochrome),
            "face_count": int(len(faces_detected)),
            "face_boxes": [[int(coord) for coord in b] for b in faces_detected],
            "detected_problems": [str(p) for p in detected_problems],
            "analysis_duration_sec": float(duration),
        }

        return img, metrics
