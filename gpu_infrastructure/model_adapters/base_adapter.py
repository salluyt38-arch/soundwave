"""
Base Adapter Interface for Modular AI Capabilities.
Every adapter implements a standard, inspectable execute method.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
from PIL import Image


class BaseCapabilityAdapter(ABC):
    """Abstract base class for all AI capability adapters."""

    def __init__(self, model_id: str, name: str, category: str):
        self.model_id = model_id
        self.name = name
        self.category = category

    @abstractmethod
    def execute(self, img: Image.Image, **kwargs) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Executes real inference on the input PIL Image.
        Returns (result_img, metrics_dict).
        """
        pass
