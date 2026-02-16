from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class PredictionResult:
    text: str
    usage: Any
    raw_response: Any = None

class ModelInterface(ABC):
    """
    Abstract base class for OCR models.
    Users can extend this class to add support for other models.
    """

    @abstractmethod
    def call(self, prompt: str, system_instruction: str, image_path: Optional[str] = None) -> PredictionResult:
        """
        Calls the model with the given prompt and optional image.

        Args:
            prompt (str): The prompt to send to the model.
            system_instruction (str): System instructions for the model.
            image_path (str, optional): Path to the image file (PDF/Image).

        Returns:
            PredictionResult: An object containing the generated text and usage statistics.
        """
        pass

    @abstractmethod
    def calculate_cost(self, usage: Any) -> float:
        """
        Calculates the cost of the call based on the usage statistics.

        Args:
            usage (Any): The usage statistics returned by the `call` method.

        Returns:
            float: The calculated cost in USD.
        """
        pass
