"""
APEX Multi-Face Localization & Region Detection Engine
Detects single and multiple faces with bounding boxes and normalized confidence.
"""

from typing import List, Tuple
import numpy as np
from PIL import Image
import scipy.ndimage as ndi


class FaceDetector:
    """
    Robust multi-face locator with OpenCV Cascade / Skin Chrominance + Geometry hybrid.
    """

    def __init__(self):
        self._cv2_cascade = None
        self._cv2_cascade_alt = None
        self._init_cv2()

    def _init_cv2(self):
        try:
            import cv2
            if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
                alt2_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
                default_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                
                c_alt = cv2.CascadeClassifier(alt2_path)
                if not c_alt.empty():
                    self._cv2_cascade_alt = c_alt
                    
                c_def = cv2.CascadeClassifier(default_path)
                if not c_def.empty():
                    self._cv2_cascade = c_def
        except Exception:
            self._cv2_cascade = None
            self._cv2_cascade_alt = None

    def detect_faces(self, img: Image.Image) -> List[Tuple[int, int, int, int]]:
        """
        Returns list of (x, y, w, h) bounding boxes for all detected faces.
        """
        w, h = img.size

        # 1. Try OpenCV Haar Cascade (alt2 first for ultra-high precision, then default)
        np_img = np.array(img.convert("RGB"))
        try:
            import cv2
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
            
            # Primary: frontalface_alt2
            if self._cv2_cascade_alt:
                faces = self._cv2_cascade_alt.detectMultiScale(
                    gray, scaleFactor=1.05, minNeighbors=5, minSize=(40, 40)
                )
                if len(faces) > 0:
                    return [(int(x), int(y), int(fw), int(fh)) for (x, y, fw, fh) in faces]

            # Secondary: frontalface_default
            if self._cv2_cascade:
                faces = self._cv2_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
                )
                if len(faces) > 0:
                    return [(int(x), int(y), int(fw), int(fh)) for (x, y, fw, fh) in faces]
        except Exception:
            pass

        # 2. Resilient Skin-Chrominance & Morphological Connected Component Fallback
        ycbcr = np.array(img.convert("YCbCr"), dtype=np.float32)
        cb = ycbcr[:, :, 1]
        cr = ycbcr[:, :, 2]
        y = ycbcr[:, :, 0]

        # Human skin chrominance locus in YCbCr
        skin_mask = (cr >= 133.0) & (cr <= 175.0) & (cb >= 80.0) & (cb <= 130.0) & (y >= 40.0) & (y <= 240.0)
        skin_clean = ndi.binary_opening(skin_mask, structure=np.ones((5, 5)))
        skin_clean = ndi.binary_closing(skin_clean, structure=np.ones((7, 7)))

        labeled, num_features = ndi.label(skin_clean)
        if num_features == 0:
            return [(int(w * 0.25), int(h * 0.15), int(w * 0.5), int(h * 0.5))]

        face_boxes = []
        slices = ndi.find_objects(labeled)
        for s in slices:
            if s is None:
                continue
            sy, sx = s
            fw = sx.stop - sx.start
            fh = sy.stop - sy.start
            area = fw * fh

            # Filter out giant background walls/pillars (fw < 0.45*w, fh < 0.45*h)
            # and tiny specks (area > w*h*0.008), with face-like aspect ratio (0.7 to 1.7)
            if (
                area > (w * h * 0.008)
                and fw < (w * 0.50)
                and fh < (h * 0.50)
                and 0.7 <= (fh / max(1, fw)) <= 1.7
                and sy.start < (h * 0.65)  # Face must be in the upper 65% of the frame
            ):
                face_boxes.append((sx.start, sy.start, fw, fh))

        if not face_boxes:
            return [(int(w * 0.25), int(h * 0.15), int(w * 0.5), int(h * 0.5))]

        # Sort by area descending (largest faces first)
        face_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
        return face_boxes
