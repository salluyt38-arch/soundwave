"""
Face Analysis & Landmark Extraction Engine.
Extracts facial boundaries, eye regions, eyebrows, lips, nose, beard/moustache,
hair boundaries, skin regions, and lighting metrics without gender classification.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("gpu_infrastructure.beauty.face_analyzer")


@dataclass
class FaceGeometry:
    """Detailed structural landmark and region bounds for a single detected face."""
    face_box: Tuple[int, int, int, int]  # (x, y, w, h)
    left_eye: Optional[Tuple[int, int]] = None  # (cx, cy)
    right_eye: Optional[Tuple[int, int]] = None  # (cx, cy)
    left_eye_box: Optional[Tuple[int, int, int, int]] = None
    right_eye_box: Optional[Tuple[int, int, int, int]] = None
    nose_tip: Optional[Tuple[int, int]] = None
    mouth_center: Optional[Tuple[int, int]] = None
    mouth_box: Optional[Tuple[int, int, int, int]] = None
    eyebrow_boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)
    jawline_points: List[Tuple[int, int]] = field(default_factory=list)
    has_facial_hair: bool = False
    facial_hair_mask: Optional[np.ndarray] = None


@dataclass
class LightingMetrics:
    """Photometric lighting condition analysis of the portrait."""
    mean_luminance: float
    contrast_rms: float
    shadow_clipping_pct: float
    highlight_clipping_pct: float
    condition: str  # 'balanced', 'underexposed', 'overexposed', 'high_contrast', 'soft_diffuse'


@dataclass
class FaceAnalysisResult:
    """Complete face-aware analysis payload for downstream beauty and adaptive filters."""
    faces: List[FaceGeometry]
    skin_mask: np.ndarray  # uint8 binary mask: 255 = skin, 0 = non-skin / hair / background
    feature_preservation_mask: np.ndarray  # uint8: 255 = keep 100% sharp (eyes, beard, hair, lips)
    lighting: LightingMetrics
    image_width: int
    image_height: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "face_count": len(self.faces),
            "faces": [
                {
                    "box": list(f.face_box),
                    "left_eye": list(f.left_eye) if f.left_eye else None,
                    "right_eye": list(f.right_eye) if f.right_eye else None,
                    "nose_tip": list(f.nose_tip) if f.nose_tip else None,
                    "mouth_center": list(f.mouth_center) if f.mouth_center else None,
                    "has_facial_hair": f.has_facial_hair,
                }
                for f in self.faces
            ],
            "lighting": {
                "mean_luminance": round(self.lighting.mean_luminance, 1),
                "contrast_rms": round(self.lighting.contrast_rms, 1),
                "shadow_clipping_pct": round(self.lighting.shadow_clipping_pct, 2),
                "highlight_clipping_pct": round(self.lighting.highlight_clipping_pct, 2),
                "condition": self.lighting.condition,
            },
            "image_dimensions": [self.image_width, self.image_height],
        }


class FaceAnalyzer:
    """
    Intelligent face detector, landmarker, and skin/hair/beard segmenter.
    Adheres strictly to zero automated gender classification.
    """

    def __init__(self):
        # Load high-accuracy cascades from bundled OpenCV data
        haar_dir = getattr(cv2, "data", None)
        haar_path = haar_dir.haarcascades if haar_dir else ""
        
        self.face_cascade = cv2.CascadeClassifier(haar_path + "haarcascade_frontalface_default.xml")
        self.profile_cascade = cv2.CascadeClassifier(haar_path + "haarcascade_profileface.xml")
        self.eye_cascade = cv2.CascadeClassifier(haar_path + "haarcascade_eye.xml")
        self.smile_cascade = cv2.CascadeClassifier(haar_path + "haarcascade_smile.xml")

    def analyze(self, image: Image.Image) -> FaceAnalysisResult:
        """
        Runs comprehensive facial structure, skin locus, hair boundary,
        and lighting analysis on a PIL Image.
        """
        rgb_np = np.array(image.convert("RGB"))
        h, w = rgb_np.shape[:2]
        gray = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2GRAY)

        # 1. Detect faces
        faces = self._detect_faces(gray, w, h)

        # 2. Extract detailed landmarks and facial hair for each face
        geometries: List[FaceGeometry] = []
        for face_box in faces:
            geo = self._extract_landmarks(gray, rgb_np, face_box)
            geometries.append(geo)

        # 3. Multi-color-space skin segmentation
        raw_skin_mask = self._segment_skin(rgb_np)

        # 4. Generate preservation mask: protect eyes, lips, eyebrows, beard, and hair from blurring
        preservation_mask = np.zeros((h, w), dtype=np.uint8)
        for geo in geometries:
            fx, fy, fw, fh = geo.face_box

            # Preserve eyes
            if geo.left_eye_box:
                ex, ey, ew, eh = geo.left_eye_box
                cv2.ellipse(preservation_mask, (ex + ew // 2, ey + eh // 2), (int(ew * 0.7), int(eh * 0.7)), 0, 0, 360, 255, -1)
            elif geo.left_eye:
                cv2.circle(preservation_mask, geo.left_eye, max(6, int(fw * 0.08)), 255, -1)

            if geo.right_eye_box:
                ex, ey, ew, eh = geo.right_eye_box
                cv2.ellipse(preservation_mask, (ex + ew // 2, ey + eh // 2), (int(ew * 0.7), int(eh * 0.7)), 0, 0, 360, 255, -1)
            elif geo.right_eye:
                cv2.circle(preservation_mask, geo.right_eye, max(6, int(fw * 0.08)), 255, -1)

            # Preserve eyebrows
            for ebx, eby, ebw, ebh in geo.eyebrow_boxes:
                cv2.rectangle(preservation_mask, (ebx, eby), (ebx + ebw, eby + ebh), 255, -1)

            # Preserve lips and mouth
            if geo.mouth_box:
                mx, my, mw, mh = geo.mouth_box
                cv2.ellipse(preservation_mask, (mx + mw // 2, my + mh // 2), (int(mw * 0.6), int(mh * 0.6)), 0, 0, 360, 255, -1)
            elif geo.mouth_center:
                cv2.ellipse(preservation_mask, geo.mouth_center, (int(fw * 0.16), int(fh * 0.08)), 0, 0, 360, 255, -1)

            # Preserve facial hair / beard regions
            if geo.has_facial_hair and geo.facial_hair_mask is not None:
                preservation_mask = cv2.bitwise_or(preservation_mask, geo.facial_hair_mask)

        # 5. Extract hair boundary / high-frequency texture outside skin
        edges = cv2.Canny(gray, 60, 160)
        dilated_edges = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        # Intersect edges with high contrast hair areas
        hair_boundary = cv2.bitwise_and(dilated_edges, cv2.bitwise_not(raw_skin_mask))
        preservation_mask = cv2.bitwise_or(preservation_mask, hair_boundary)

        # 6. Final pure skin mask = (Skin locus) AND NOT (Preservation regions)
        final_skin_mask = cv2.bitwise_and(raw_skin_mask, cv2.bitwise_not(preservation_mask))
        # Smooth skin mask boundary to prevent harsh seam transitions
        final_skin_mask = cv2.GaussianBlur(final_skin_mask, (7, 7), 0)

        # 7. Analyze Lighting Conditions
        lighting = self._analyze_lighting(gray)

        return FaceAnalysisResult(
            faces=geometries,
            skin_mask=final_skin_mask,
            feature_preservation_mask=preservation_mask,
            lighting=lighting,
            image_width=w,
            image_height=h,
        )

    def _detect_faces(self, gray: np.ndarray, w: int, h: int) -> List[Tuple[int, int, int, int]]:
        """Multi-pass face locator with scale-invariance."""
        min_dim = min(w, h)
        min_size = (max(24, int(min_dim * 0.08)), max(24, int(min_dim * 0.08)))

        # Frontal pass
        detected = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=min_size
        )
        faces = [tuple(map(int, f)) for f in detected] if len(detected) > 0 else []

        # Profile fallback if no frontal face found
        if not faces and not self.profile_cascade.empty():
            p_detected = self.profile_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=min_size
            )
            if len(p_detected) > 0:
                faces = [tuple(map(int, f)) for f in p_detected]

        return faces

    def _extract_landmarks(self, gray: np.ndarray, rgb: np.ndarray, box: Tuple[int, int, int, int]) -> FaceGeometry:
        """Extracts eyes, eyebrows, nose, mouth, and beard regions inside the face bounding box."""
        fx, fy, fw, fh = box
        face_gray = gray[fy : fy + fh, fx : fx + fw]
        face_rgb = rgb[fy : fy + fh, fx : fx + fw]

        geo = FaceGeometry(face_box=box)

        # 1. Eyes Detection in upper 55% of the face
        upper_h = int(fh * 0.55)
        upper_gray = face_gray[0:upper_h, :]
        detected_eyes = self.eye_cascade.detectMultiScale(
            upper_gray, scaleFactor=1.1, minNeighbors=4, minSize=(max(12, int(fw * 0.12)), max(12, int(fh * 0.10)))
        )

        left_eye_box = None
        right_eye_box = None

        if len(detected_eyes) >= 2:
            # Sort by X coordinate (left eye vs right eye from viewer's perspective)
            sorted_eyes = sorted(detected_eyes, key=lambda e: e[0])
            e1 = sorted_eyes[0]
            e2 = sorted_eyes[-1]
            if (e2[0] - e1[0]) > (fw * 0.18):
                left_eye_box = (fx + int(e1[0]), fy + int(e1[1]), int(e1[2]), int(e1[3]))
                right_eye_box = (fx + int(e2[0]), fy + int(e2[1]), int(e2[2]), int(e2[3]))

        # Geometric estimate if Haar didn't resolve both distinct eyes
        if not left_eye_box:
            left_eye_box = (fx + int(fw * 0.20), fy + int(fh * 0.32), int(fw * 0.22), int(fh * 0.16))
        if not right_eye_box:
            right_eye_box = (fx + int(fw * 0.58), fy + int(fh * 0.32), int(fw * 0.22), int(fh * 0.16))

        geo.left_eye_box = left_eye_box
        geo.right_eye_box = right_eye_box
        geo.left_eye = (left_eye_box[0] + left_eye_box[2] // 2, left_eye_box[1] + left_eye_box[3] // 2)
        geo.right_eye = (right_eye_box[0] + right_eye_box[2] // 2, right_eye_box[1] + right_eye_box[3] // 2)

        # Eyebrows: regions directly above the eyes
        geo.eyebrow_boxes = [
            (left_eye_box[0] - 2, max(0, left_eye_box[1] - int(fh * 0.12)), left_eye_box[2] + 4, int(fh * 0.12)),
            (right_eye_box[0] - 2, max(0, right_eye_box[1] - int(fh * 0.12)), right_eye_box[2] + 4, int(fh * 0.12)),
        ]

        # 2. Nose tip (geometric center between eyes and mouth)
        geo.nose_tip = (fx + fw // 2, fy + int(fh * 0.58))

        # 3. Mouth / Lips detection in lower 40% of the face
        lower_y = int(fh * 0.60)
        lower_gray = face_gray[lower_y:, :]
        detected_smiles = self.smile_cascade.detectMultiScale(
            lower_gray, scaleFactor=1.15, minNeighbors=8, minSize=(int(fw * 0.25), int(fh * 0.10))
        )
        if len(detected_smiles) > 0:
            best_mouth = sorted(detected_smiles, key=lambda s: s[2] * s[3], reverse=True)[0]
            mx, my, mw, mh = best_mouth
            geo.mouth_box = (fx + int(mx), fy + lower_y + int(my), int(mw), int(mh))
            geo.mouth_center = (geo.mouth_box[0] + mw // 2, geo.mouth_box[1] + mh // 2)
        else:
            geo.mouth_center = (fx + fw // 2, fy + int(fh * 0.78))
            geo.mouth_box = (fx + int(fw * 0.32), fy + int(fh * 0.72), int(fw * 0.36), int(fh * 0.16))

        # 4. Jawline contour approximation
        geo.jawline_points = [
            (fx + int(fw * 0.10), fy + int(fh * 0.65)),
            (fx + int(fw * 0.20), fy + int(fh * 0.82)),
            (fx + int(fw * 0.35), fy + int(fh * 0.94)),
            (fx + int(fw * 0.50), fy + int(fh * 0.98)),
            (fx + int(fw * 0.65), fy + int(fh * 0.94)),
            (fx + int(fw * 0.80), fy + int(fh * 0.82)),
            (fx + int(fw * 0.90), fy + int(fh * 0.65)),
        ]

        # 5. Facial Hair / Beard & Moustache Detection
        # Analyzes texture variance and luminance in the lower jaw and upper lip regions
        lower_face_rgb = face_rgb[int(fh * 0.62) :, int(fw * 0.15) : int(fw * 0.85)]
        if lower_face_rgb.size > 0:
            hsv_lower = cv2.cvtColor(lower_face_rgb, cv2.COLOR_RGB2HSV)
            val_lower = hsv_lower[:, :, 2]
            laplacian_var = cv2.Laplacian(val_lower, cv2.CV_64F).var()

            # High micro-texture and lower brightness indicates presence of beard / stubble
            if laplacian_var > 120.0 or np.mean(val_lower) < 95.0:
                geo.has_facial_hair = True
                hair_mask = np.zeros(gray.shape, dtype=np.uint8)
                # Mark lower jaw region as preserved beard region
                pts = np.array(
                    [
                        [fx + int(fw * 0.18), fy + int(fh * 0.64)],
                        [fx + int(fw * 0.82), fy + int(fh * 0.64)],
                        [fx + int(fw * 0.85), fy + int(fh * 0.98)],
                        [fx + int(fw * 0.15), fy + int(fh * 0.98)],
                    ],
                    np.int32,
                )
                cv2.fillPoly(hair_mask, [pts], 255)
                geo.facial_hair_mask = hair_mask

        return geo

    def _segment_skin(self, rgb: np.ndarray) -> np.ndarray:
        """
        Robust dual-space skin locus segmentation (YCbCr + HSV).
        Effectively separates living human skin tones from clothing, background, and hair.
        """
        # 1. YCbCr Locus
        ycbcr = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
        y = ycbcr[:, :, 0]
        cr = ycbcr[:, :, 1]
        cb = ycbcr[:, :, 2]
        skin_ycbcr = (y > 45) & (cb >= 77) & (cb <= 130) & (cr >= 132) & (cr <= 178)

        # 2. HSV Locus
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        h = hsv[:, :, 0]
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        skin_hsv = ((h <= 25) | (h >= 165)) & (s >= 20) & (s <= 185) & (v >= 45)

        # Combined intersection
        combined = (skin_ycbcr & skin_hsv).astype(np.uint8) * 255

        # Morphological opening and closing to remove noise and fill pores
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        opened = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel_open)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)

        return closed

    def _analyze_lighting(self, gray: np.ndarray) -> LightingMetrics:
        """Extracts statistical luminance, dynamic range, and highlight/shadow clipping."""
        mean_lum = float(np.mean(gray))
        contrast_rms = float(np.std(gray))
        total_px = gray.size

        shadow_clipping = float(np.sum(gray < 15) / total_px * 100.0)
        highlight_clipping = float(np.sum(gray > 242) / total_px * 100.0)

        # Determine qualitative lighting condition
        if mean_lum < 70 and shadow_clipping > 10.0:
            condition = "underexposed"
        elif mean_lum > 175 and highlight_clipping > 8.0:
            condition = "overexposed"
        elif contrast_rms > 65.0:
            condition = "high_contrast"
        elif contrast_rms < 32.0:
            condition = "soft_diffuse"
        else:
            condition = "balanced"

        return LightingMetrics(
            mean_luminance=mean_lum,
            contrast_rms=contrast_rms,
            shadow_clipping_pct=shadow_clipping,
            highlight_clipping_pct=highlight_clipping,
            condition=condition,
        )
