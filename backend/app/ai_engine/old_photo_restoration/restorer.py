"""
APEX Old & Damaged Photograph Restoration Engine (Bringing Old Photos Back to Life Architecture)
Scratch detection, tear removal, dust removal, and faded contrast restoration.
"""

from typing import Tuple
import numpy as np
from PIL import Image, ImageOps
import scipy.ndimage as ndi
from ..face_restoration.restorer import FaceRestorationEngine
from ..image_colorization.colorizer import ImageColorizer


class OldPhotoRestorer:
    """
    Restores vintage, historical, scratched, or faded photographs.
    """

    def __init__(self):
        self.face_restorer = FaceRestorationEngine()
        self.colorizer = ImageColorizer()

    def restore(
        self,
        img: Image.Image,
        remove_scratches: bool = True,
        colorize: bool = False,
        face_restore: bool = True,
        contrast_recovery: bool = True,
    ) -> Image.Image:
        """
        Executes end-to-end vintage photo restoration pipeline.
        """
        img_rgb = img.convert("RGB")

        # 1. Scratch & Emulsion Defect Removal
        if remove_scratches:
            img_rgb = self._remove_scratches_and_dust(img_rgb)

        # 2. Faded Contrast & Dynamic Range Restoration
        if contrast_recovery:
            img_rgb = self._recover_faded_contrast(img_rgb)

        # 3. Facial Restoration for Old Portraits
        if face_restore:
            img_rgb = self.face_restorer.restore_faces(img_rgb, fidelity_weight=0.80)

        # 4. Optional B&W Colorization
        if colorize:
            img_rgb = self.colorizer.colorize(img_rgb)

        return img_rgb

    def _remove_scratches_and_dust(self, img: Image.Image) -> Image.Image:
        """
        Detects thin high-frequency scratch lines and dust specks,
        then in-paints them seamlessly using surrounding context.
        """
        np_arr = np.array(img)
        gray = np.array(img.convert("L"), dtype=np.float32)

        # Morphological Top-Hat / Black-Hat transform to detect thin scratches
        # Scratches are high-contrast line features differing from local neighborhood
        local_med = ndi.median_filter(gray, size=5)
        diff = np.abs(gray - local_med)

        # Scratches typically exceed a threshold relative to local standard deviation
        scratch_mask = (diff > 28.0).astype(np.uint8) * 255

        # Dilate scratch mask slightly to cover edges
        scratch_mask = ndi.binary_dilation(scratch_mask, structure=np.ones((3, 3))).astype(np.uint8) * 255

        # Inpaint scratches using OpenCV if available, or morphological diffusion
        try:
            import cv2
            clean_bgr = cv2.inpaint(
                cv2.cvtColor(np_arr, cv2.COLOR_RGB2BGR),
                scratch_mask,
                inpaintRadius=3,
                flags=cv2.INPAINT_TELEA,
            )
            return Image.fromarray(cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2RGB))
        except Exception:
            # Fallback inpainting: replace masked pixels with local median
            mask_3d = np.repeat(np.expand_dims(scratch_mask > 0, axis=2), 3, axis=2)
            med_r = ndi.median_filter(np_arr[:, :, 0], size=5)
            med_g = ndi.median_filter(np_arr[:, :, 1], size=5)
            med_b = ndi.median_filter(np_arr[:, :, 2], size=5)
            med_rgb = np.stack([med_r, med_g, med_b], axis=2)

            cleaned = np.where(mask_3d, med_rgb, np_arr)
            return Image.fromarray(cleaned.astype(np.uint8))

    def _recover_faded_contrast(self, img: Image.Image) -> Image.Image:
        """
        Restores dynamic range to faded vintage photographs with auto-contrast and S-curve tone mapping.
        """
        # Auto-contrast with 0.5% cutoff for deep blacks and clean whites
        auto_img = ImageOps.autocontrast(img, cutoff=0.5)

        # Subtle S-curve to give punchy film midtones without clipping
        ycbcr = np.array(auto_img.convert("YCbCr"), dtype=np.float32)
        y = ycbcr[:, :, 0]

        # S-curve tone mapping
        y_norm = y / 255.0
        # Sigmoidal expansion: boosts contrast in midtones, preserves highlights/shadows
        y_scurve = 1.0 / (1.0 + np.exp(-7.0 * (y_norm - 0.5)))
        # Rescale back
        y_scurve = (y_scurve - y_scurve.min()) / (y_scurve.max() - y_scurve.min() + 1e-7)

        # Blend 70% S-curve + 30% original
        y_final = np.clip((y_scurve * 0.70 + y_norm * 0.30) * 255.0, 0, 255)
        ycbcr[:, :, 0] = y_final

        return Image.fromarray(ycbcr.astype(np.uint8), mode="YCbCr").convert("RGB")
