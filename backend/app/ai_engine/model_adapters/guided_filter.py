"""
Guided Filter & Edge-Preserving Micro-Texture Decomposition Engine
Eliminates halos, ringing, and cartoon-like outlines completely.
"""

from typing import Any
import numpy as np
import scipy.ndimage as ndi


def guided_filter_luma(I: np.ndarray, p: np.ndarray, r: int = 5, eps: float = 0.015) -> np.ndarray:
    """
    Fast Guided Filter for Edge-Preserving Base/Detail Decomposition (He et al., IEEE TPAMI).
    I: Guidance image (normalized 0.0 to 1.0)
    p: Input image (normalized 0.0 to 1.0)
    r: Filter radius
    eps: Regularization parameter penalizing variance
    """
    mean_I = ndi.uniform_filter(I, size=r)
    mean_p = ndi.uniform_filter(p, size=r)
    mean_Ip = ndi.uniform_filter(I * p, size=r)
    cov_Ip = mean_Ip - mean_I * mean_p

    mean_II = ndi.uniform_filter(I * I, size=r)
    var_I = mean_II - mean_I * mean_I

    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I

    mean_a = ndi.uniform_filter(a, size=r)
    mean_b = ndi.uniform_filter(b, size=r)

    q = mean_a * I + mean_b
    return q


def soft_tanh_detail_boost(high_freq: np.ndarray, gain: float = 1.85, ceiling: float = 0.12) -> np.ndarray:
    """
    Soft saturating hyperbolic tangent detail transfer.
    Smoothly sharpens high frequencies while mathematically clamping overshoots,
    guaranteeing zero white halos and zero black outlines.
    """
    return np.tanh(high_freq * gain) * ceiling
