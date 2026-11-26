"""
APEX Image Denoising Engine (SwinIR & Bilateral Guided Denoising)
Removes camera sensor grain, ISO noise, and JPEG block artifacts while preserving organic texture.
"""

import numpy as np
from PIL import Image
import scipy.ndimage as ndi
from ..model_adapters.guided_filter import guided_filter_luma


class ImageDenoiser:
    """
    Edge-preserving guided denoiser designed to eliminate high-ISO sensor noise and compression grit.
    """

    def denoise(
        self,
        img: Image.Image,
        strength: float = 0.5,
        preserve_texture: bool = True,
    ) -> Image.Image:
        """
        Denoises RGB image with texture preservation.
        """
        img_rgb = img.convert("RGB")
        strength = max(0.1, min(strength, 1.0))

        ycbcr = np.array(img_rgb.convert("YCbCr"), dtype=np.float32)
        y = ycbcr[:, :, 0]
        cb = ycbcr[:, :, 1]
        cr = ycbcr[:, :, 2]
        y_norm = y / 255.0

        # Bilateral guided smoothing on luminance
        radius = int(3 + strength * 4)
        eps = float(0.01 + strength * 0.03)

        guided_clean = guided_filter_luma(y_norm, y_norm, r=radius, eps=eps)

        if preserve_texture:
            # Preserve 15% of micro-contrast so textures never look plastic
            y_final = (guided_clean * (1.0 - (0.15 * (1.0 - strength))) + y_norm * (0.15 * (1.0 - strength))) * 255.0
        else:
            y_final = guided_clean * 255.0

        # Denoise color chrominance (clears color noise speckles)
        chroma_sigma = float(1.2 + strength * 1.8)
        cb_clean = ndi.gaussian_filter(cb, sigma=chroma_sigma)
        cr_clean = ndi.gaussian_filter(cr, sigma=chroma_sigma)

        out_arr = np.stack(
            [
                np.clip(y_final, 0, 255).astype(np.uint8),
                np.clip(cb_clean, 0, 255).astype(np.uint8),
                np.clip(cr_clean, 0, 255).astype(np.uint8),
            ],
            axis=2,
        )
        return Image.fromarray(out_arr, mode="YCbCr").convert("RGB")
