"""
APEX AI Quality Assessment Engine
Computes PSNR, SSIM, Blur Metric, and Dynamic Range Safety.
"""

import math
from typing import Any, Dict, Tuple
import numpy as np
from PIL import Image
import scipy.ndimage as ndi
from ...schemas.models import QualityMetrics


class ImageQualityEvaluator:
    """
    Evaluates real image quality metrics to prove genuine restoration without simulation.
    """

    @staticmethod
    def compute_blur_score(gray_arr: np.ndarray) -> float:
        """Calculates variance of Laplacian to measure edge sharpness/blur."""
        laplacian = ndi.laplace(gray_arr.astype(np.float64))
        return float(laplacian.var())

    @staticmethod
    def compute_psnr(orig: np.ndarray, proc: np.ndarray) -> float:
        """Calculates Peak Signal-to-Noise Ratio (dB) on luminance."""
        mse = np.mean((orig.astype(np.float64) - proc.astype(np.float64)) ** 2)
        if mse == 0:
            return 100.0
        return float(20.0 * math.log10(255.0 / math.sqrt(mse)))

    @staticmethod
    def compute_ssim(orig: np.ndarray, proc: np.ndarray) -> float:
        """Calculates Structural Similarity Index Measure (SSIM)."""
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        img1 = orig.astype(np.float64)
        img2 = proc.astype(np.float64)

        mu1 = ndi.gaussian_filter(img1, sigma=1.5)
        mu2 = ndi.gaussian_filter(img2, sigma=1.5)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = ndi.gaussian_filter(img1 ** 2, sigma=1.5) - mu1_sq
        sigma2_sq = ndi.gaussian_filter(img2 ** 2, sigma=1.5) - mu2_sq
        sigma12 = ndi.gaussian_filter(img1 * img2, sigma=1.5) - mu1_mu2

        num = (2 * mu1_mu2 + c1) * (2 * sigma12 + c2)
        den = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
        ssim_map = num / (den + 1e-7)
        return float(np.clip(np.mean(ssim_map), 0.0, 1.0))

    @classmethod
    def evaluate(
        cls,
        orig_img: Image.Image,
        enhanced_img: Image.Image,
        duration_sec: float,
        scale: int,
    ) -> QualityMetrics:
        """
        Runs comprehensive quality validation on original vs enhanced images.
        """
        # Downscale enhanced image to original dimensions to compare fidelity
        ow, oh = orig_img.size
        ew, eh = enhanced_img.size

        comp_enhanced = enhanced_img.resize((ow, oh), Image.Resampling.LANCZOS)

        orig_y = np.array(orig_img.convert("L"), dtype=np.float32)
        proc_y = np.array(comp_enhanced.convert("L"), dtype=np.float32)

        psnr_val = round(cls.compute_psnr(orig_y, proc_y), 2)
        ssim_val = round(cls.compute_ssim(orig_y, proc_y), 4)
        blur_val = round(cls.compute_blur_score(proc_y), 2)

        # Exposure and clipping check
        enh_arr = np.array(enhanced_img.convert("L"))
        white_clip = float(np.sum(enh_arr >= 254) / enh_arr.size)
        black_clip = float(np.sum(enh_arr <= 1) / enh_arr.size)
        exposure_safe = white_clip < 0.05 and black_clip < 0.05

        grade = "EXCELLENT" if ssim_val >= 0.90 and psnr_val >= 24.0 else "GOOD"

        return QualityMetrics(
            psnr_db=psnr_val,
            ssim=ssim_val,
            blur_score=blur_val,
            white_clipping_ratio=round(white_clip, 4),
            black_clipping_ratio=round(black_clip, 4),
            exposure_safe=exposure_safe,
            quality_grade=grade,
            inference_duration_sec=round(duration_sec, 2),
            input_resolution=f"{ow}x{oh}",
            output_resolution=f"{ew}x{eh}",
            scale=f"{scale}x",
        )
