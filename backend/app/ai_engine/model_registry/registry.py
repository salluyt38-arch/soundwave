"""
APEX AI Model Registry & Upstream Open-Source Repository Catalog
Enforces rigorous license tracking, device compatibility, and hardware capabilities.
"""

from typing import Dict, List, Optional
from ...schemas.models import ModelInfo


class AIModelRegistry:
    """
    Central catalog of all AI models, architectures, licenses, and repositories.
    """

    _MODELS: Dict[str, ModelInfo] = {
        "real-esrgan": ModelInfo(
            model_id="real-esrgan",
            display_name="Real-ESRGAN (x4plus / x2plus)",
            category="Super-Resolution & Upscaling",
            upstream_repository="https://github.com/xinntao/Real-ESRGAN",
            license_type="BSD-3-Clause",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Multi-scale residual super-resolution engine for 2x/4x image detail recovery and edge sharpness."
        ),
        "gfpgan": ModelInfo(
            model_id="gfpgan",
            display_name="GFPGAN v1.4 Facial Restoration",
            category="Face Restoration",
            upstream_repository="https://github.com/TencentARC/GFPGAN",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Blind facial restoration restoring eyes, iris sparkle, lip vermilion, and smooth skin tones."
        ),
        "codeformer": ModelInfo(
            model_id="codeformer",
            display_name="CodeFormer Robust Face Restoration",
            category="Face Restoration & Quality Control",
            upstream_repository="https://github.com/sczhou/CodeFormer",
            license_type="S-Lab License (Academic/Non-Commercial Pretrained)",
            commercial_friendly=False,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Codebook lookup transformer for severe facial degradation and controllable fidelity."
        ),
        "swinir": ModelInfo(
            model_id="swinir",
            display_name="SwinIR Image Restoration",
            category="Denoising & Super-Resolution",
            upstream_repository="https://github.com/JingyunLiang/SwinIR",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Swin Transformer for image super-resolution, JPEG compression artifact removal, and denoising."
        ),
        "restoreformer": ModelInfo(
            model_id="restoreformer",
            display_name="RestoreFormer Blind Face Restoration",
            category="Face Restoration",
            upstream_repository="https://github.com/wzhouxiff/RestoreFormer",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Multi-head cross-attention face transformer restoring structural high-frequency details."
        ),
        "bringing-old-photos": ModelInfo(
            model_id="bringing-old-photos",
            display_name="Microsoft Bringing Old Photos Back to Life",
            category="Old Photo Restoration",
            upstream_repository="https://github.com/microsoft/Bringing-Old-Photos-Back-to-Life",
            license_type="MIT",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Deep latent space scratch detection, tear removal, and faded vintage photograph restoration."
        ),
        "lama": ModelInfo(
            model_id="lama",
            display_name="LaMa Large Mask Inpainting",
            category="Object Removal & Inpainting",
            upstream_repository="https://github.com/advimman/lama",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Fast Fourier Convolution (FFC) inpainting for object erasure, scratch filling, and text removal."
        ),
        "colorization": ModelInfo(
            model_id="colorization",
            display_name="Colorful Image Colorization (Zhang et al.)",
            category="Colorization",
            upstream_repository="https://github.com/richzhang/colorization",
            license_type="BSD-2-Clause",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Luminance-to-Chrominance deep neural mapping for realistic black & white photo colorization."
        ),
        "basicsr": ModelInfo(
            model_id="basicsr",
            display_name="BasicSR Toolbox",
            category="AI Infrastructure",
            upstream_repository="https://github.com/XPixelGroup/BasicSR",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Foundational image and video restoration toolbox powering modern tensor pipelines."
        ),
        "opencv": ModelInfo(
            model_id="opencv",
            display_name="OpenCV Computer Vision Library",
            category="Image Processing",
            upstream_repository="https://github.com/opencv/opencv",
            license_type="Apache-2.0",
            commercial_friendly=True,
            hardware_accelerated=True,
            supported_devices=["cuda", "cpu"],
            description="Core computer vision, face cascade localization, morphological filtering, and inpainting algorithms."
        ),
        "pillow": ModelInfo(
            model_id="pillow",
            display_name="Pillow Imaging Library",
            category="Image Manipulation",
            upstream_repository="https://github.com/python-pillow/Pillow",
            license_type="HPND",
            commercial_friendly=True,
            hardware_accelerated=False,
            supported_devices=["cpu"],
            description="Fundamental image manipulation, EXIF orientation correction, and format conversions."
        )
    }

    @classmethod
    def get_all_models(cls) -> List[ModelInfo]:
        return list(cls._MODELS.values())

    @classmethod
    def get_model(cls, model_id: str) -> Optional[ModelInfo]:
        return cls._MODELS.get(model_id.lower().strip())

    @classmethod
    def get_commercial_friendly_models(cls) -> List[ModelInfo]:
        return [m for m in cls._MODELS.values() if m.commercial_friendly]
