"""
Command-line interface for fonix_ocr_bench
"""
import os
import argparse
import dotenv
from google.genai import types
from .model_interface import ModelInterface
from .gemini_model import GeminiModel
from .dataset import BenchmarkDataset
from .runner import BenchmarkRunner

# Load environment variables
dotenv.load_dotenv()

# Configuration
SYSTEM_INSTRUCTION = "You are a experienced annotater who can identify student answers for a student's paper and complete the given JSON."
PROMPT_TEMPLATE = """
1. Read the uploaded document and extarct the answers and reshape according to the following structure.
2. For is is_legible use "true" if the answer is redable and not empty otherwise "false". If empty, keep blank is_legible: ""

Here is the Sturcture that you should complete:
```
{STRUCTURE_INJECTED}
```

Output must be only the completed JSON object.
"""

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Run OCR Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fonix-ocr-bench --data_dir ./data --output_dir ./results
  fonix-ocr-bench --model gemini-3-flash-preview
  
Environment Variables:
  GOOGLE_API_KEY    Google API key for Gemini models
        """
    )
    parser.add_argument("--data_dir", type=str, default="./data/all_together", help="Path to data directory")
    parser.add_argument("--output_dir", type=str, default="./results", help="Path to output directory")
    parser.add_argument("--api_key", type=str, default=os.getenv("GOOGLE_API_KEY"), help="Google API Key")
    parser.add_argument("--model", type=str, default="gemini-3-flash-preview", help="Gemini Model Name")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: API Key is required. Set GOOGLE_API_KEY env var or pass --api_key")
        return 1

    # Initialize Components
    model = GeminiModel(api_key=args.api_key, model_name=args.model)
    
    dataset = BenchmarkDataset(data_dir=args.data_dir)
    runner = BenchmarkRunner(dataset=dataset, model=model, output_dir=args.output_dir)
    
    # Run Benchmark
    print(f"Starting Benchmark with model: {args.model}")
    runner.run(
        system_instruction=SYSTEM_INSTRUCTION,
        prompt_template=PROMPT_TEMPLATE
    )
    
    return 0

if __name__ == "__main__":
    exit(main())
