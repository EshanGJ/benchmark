import os
import pathlib
from google import genai
from google.genai import types
from .model_interface import ModelInterface, PredictionResult, UsageStats
from .logger import logger

class Gemini3Model(ModelInterface):
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview", exchange_rate: float = 310.13):
        self.api_key = api_key
        self.model_name = model_name
        self.exchange_rate = exchange_rate
        self.client = genai.Client(http_options={'api_version': 'v1alpha'}, api_key=self.api_key)
        
        # Default config from dev.ipynb
        self.thinking_level = types.ThinkingLevel.HIGH
        self.temperature = 1
        self.top_p = 0.95
        self.media_resolution = types.MediaResolution.MEDIA_RESOLUTION_HIGH

    def call(self, prompt: str, system_instruction: str, image_path: str = None, image_bytes: bytes = None) -> PredictionResult:
        """
        Calls Gemini model matching dev.ipynb implementation.
        """
        logger.debug(f"Calling Gemini ({self.model_name}) with prompt length: {len(prompt)}")
        parts = [types.Part(text=prompt)]
        
        if image_path is not None:
            filepath = pathlib.Path(image_path)
            parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=filepath.read_bytes(),
                    ),
                    media_resolution={"level": self.media_resolution}
                )
            )
        elif image_bytes is not None:
            parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/png",  # Defaulting to PNG for individual pages
                        data=image_bytes,
                    ),
                    media_resolution={"level": self.media_resolution}
                )
            )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            config=types.GenerateContentConfig(
                systemInstruction=system_instruction,
                thinking_config=types.ThinkingConfig(thinking_level=self.thinking_level),
                temperature=self.temperature,
                top_p=self.top_p
            ),
            contents=[types.Content(parts=parts)]
        )
        logger.debug("Gemini response received")
        
        u = response.usage_metadata
        usage = UsageStats(
            prompt_tokens=u.prompt_token_count,
            completion_tokens=u.candidates_token_count,
            thinking_tokens=u.thoughts_token_count if hasattr(u, 'thoughts_token_count') and u.thoughts_token_count else 0
        )

        return PredictionResult(
            text=response.text,
            usage=usage,
            raw_response=response
        )

    def calculate_cost(self, usage: UsageStats) -> float:
        """
        Calculate cost based on dev.ipynb implementation for gemini-3-flash-preview.
        """
        if self.model_name == "gemini-3-flash-preview":
            INPUT_PRICE = 0.5 / 1000000
            OUTPUT_PRICE = 3 / 1000000
        elif self.model_name == "gemini-3.1-pro-preview":
            INPUT_PRICE = 2 / 1000000
            OUTPUT_PRICE = 12 / 1000000
        else:
            raise ValueError(f"Unknown model name: {self.model_name}")

        total_cost = usage.prompt_tokens * INPUT_PRICE + (usage.completion_tokens + usage.thinking_tokens) * OUTPUT_PRICE
        return total_cost
