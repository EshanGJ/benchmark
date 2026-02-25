# fonix_ocr_bench Guide

## Overview

`fonix_ocr_bench` is a Python package for benchmarking OCR models, specifically designed for evaluating handwritten text extraction and structure filling.

## Advanced Customization

This section details how to extend the benchmark with custom models and cost functions.

### 1. Creating Custom Model Classes

To evaluate a new model (e.g., OpenAI GPT-4, Anthropic Claude, or a local LLM), create a class that inherits from `fonix_ocr_bench.ModelInterface`.

You must implement two methods:
1.  `call(self, prompt, system_instruction, image_path)`: Executes the model request.
2.  `calculate_cost(self, usage)`: Calculates the cost in USD based on usage stats.

#### Example: Mock Model (For Testing)

```python
from fonix_ocr_bench import ModelInterface, PredictionResult

class MockModel(ModelInterface):
    def call(self, prompt: str, system_instruction: str, image_path: str = None) -> PredictionResult:
        # Simulate a response
        return PredictionResult(
            text='{"test_number": "01", "student_answers": {"1": {"answer": "Mock Answer"}}}',
            usage={"input_tokens": 50, "output_tokens": 20},
            raw_response=None
        )

    def calculate_cost(self, usage: any) -> float:
        # Mock cost calculation
        return 0.0
```

#### Example: OpenAI GPT-4 Vision

```python
from fonix_ocr_bench import ModelInterface, PredictionResult
import base64
import os
from openai import OpenAI

class OpenAIModel(ModelInterface):
    def __init__(self, api_key=None, model="gpt-4-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def call(self, prompt: str, system_instruction: str, image_path: str = None) -> PredictionResult:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": [
                {"type": "text", "text": prompt}
            ]}
        ]
        
        if image_path:
            base64_image = self._encode_image(image_path)
            messages[0]["content"] += " [Image Attached]" # Simplification
            # Real implementation would attach image properly based on API docs
            
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096
        )
        
        text = response.choices[0].message.content
        usage = response.usage
        
        return PredictionResult(
            text=text,
            usage=usage,
            raw_response=response
        )

    def calculate_cost(self, usage) -> float:
        # GPT-4 Turbo pricing (example)
        INPUT_PRICE = 10.00 / 1_000_000
        OUTPUT_PRICE = 30.00 / 1_000_000
        
        input_tokens = getattr(usage, 'prompt_tokens', 0)
        output_tokens = getattr(usage, 'completion_tokens', 0)
        
        return (input_tokens * INPUT_PRICE) + (output_tokens * OUTPUT_PRICE)
```

### 2. Implementing Custom Cost Calculations

You can define complex cost logic based on the `usage` object returned by your model.

#### Example: Custom Pricing for Gemini

If you want to use a different Gemini model with different pricing, you can subclass `GeminiModel` or just modify the calculation in your custom class.

```python
class MyBudgetGemini(GeminiModel):
    def calculate_cost(self, usage):
        # Example: $0.50 per 1M input, $1.50 per 1M output
        input_cost = usage.prompt_token_count * (0.50 / 1_000_000)
        output_cost = usage.candidates_token_count * (1.50 / 1_000_000)
        return input_cost + output_cost
```

### 3. Integrating into Benchmark

Modify `run_benchmark.py` to use your custom class:

```python
# run_benchmark.py

# ... imports ...
from my_custom_models import OpenAIModel # Import your class

def main():
    # ... args parsing ...

    # Initialize your custom model
    # model = GeminiModel(...) 
    model = OpenAIModel(api_key=os.getenv("OPENAI_API_KEY"))

    dataset = BenchmarkDataset(data_dir=args.data_dir)
    runner = BenchmarkRunner(dataset=dataset, model=model, output_dir=args.output_dir)
    
    runner.run(
        system_instruction=SYSTEM_INSTRUCTION,
        prompt_template=PROMPT_TEMPLATE
    )
```

## Troubleshooting

- **JSON Errors**: Failures during `dataset` loading usually mean malformed JSON files. Check the error message for line/column numbers.
- **Import Errors**: Ensure you have installed the package (`pip install -e .` in `fonix_ocr_bench_pkg`) and are running `run_benchmark.py` from the root directory.
