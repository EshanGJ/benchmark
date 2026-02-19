import os
import pathlib
from google import genai
from google.genai import types
from .model_interface import ModelInterface, PredictionResult
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
        
        return PredictionResult(
            text=response.text,
            usage=response.usage_metadata,
            raw_response=response
        )

    def calculate_cost(self, usage) -> float:
        """
        Calculate cost based on dev.ipynb implementation for gemini-3-flash-preview.
        """
        prompt_tokens = usage.prompt_token_count
        candidates_tokens = usage.candidates_token_count
        thoughts_token_count = usage.thoughts_token_count if hasattr(usage, 'thoughts_token_count') else 0
        
        # Pricing from dev.ipynb for gemini-3-flash-preview
        IMPUT_PRICE = 0.5 / 1000000
        OUTPUT_PRICE = 3 / 1000000

        if thoughts_token_count:
            total_cost = (prompt_tokens) * IMPUT_PRICE + (candidates_tokens + thoughts_token_count) * OUTPUT_PRICE
        else:
            total_cost = (prompt_tokens) * IMPUT_PRICE + (candidates_tokens) * OUTPUT_PRICE
             
        return total_cost
