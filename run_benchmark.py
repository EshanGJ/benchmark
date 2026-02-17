import os
import argparse
import sys
import dotenv
from google.genai import types
from fonix_ocr_bench import Gemini3Model, BenchmarkDataset, BenchmarkRunner, logger

# Load environment variables
dotenv.load_dotenv()

# Configuration
SYSTEM_INSTRUCTION = "You are a experienced annotater who can identify student answers for a student's paper and complete the given JSON."
PROMPT_TEMPLATE = """
1. Read the uploaded document and extarct the answers and reshape according to the following structure.
2. For is is_illigible use "true" if the answer is redable and not empty otherwise "false". If empty, keep blank is_illigible: ""

Here is the Sturcture that you should complete:
```
{STRUCTURE_INJECTED}
```

Output must be only the completed JSON object.
"""

PAGE_BY_PAGE_PROMPT_TEMPLATE = """
1. You are provided with a single page from a student's exam paper and a previously completed JSON structure.
2. Your task is to update the JSON structure with any new answers found on this page.
3. If an answer is already present in the JSON and you find a better or more complete version on this page, update it.
4. For is_illigible use "true" if the answer is readable and not empty otherwise "false". If empty, keep blank is_illigible: ""

Previously completed JSON:
```
{PREVIOUS_JSON}
```

Output must be only the updated JSON object.
"""

def main():
    parser = argparse.ArgumentParser(description="Run OCR Benchmark")
    parser.add_argument("--data_dir", type=str, default="./data/all_together", help="Path to data directory")
    parser.add_argument("--output_dir", type=str, default="./results", help="Path to output directory")
    parser.add_argument("--api_key", type=str, default=os.getenv("GOOGLE_API_KEY"), help="Google API Key")
    parser.add_argument("--model", type=str, default="gemini-3-flash-preview", help="Gemini Model Name")
    parser.add_argument("--page_by_page", action="store_true", help="Process PDF page by page")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers for processing samples")
    
    args = parser.parse_args()
    
    if not args.api_key:
        logger.error("Error: API Key is required. Set GOOGLE_API_KEY env var or pass --api_key")
        return

    # Initialize Components
    # Note: You can replace GeminiModel with your own custom model class here.
    model = Gemini3Model(api_key=args.api_key, model_name=args.model)
    
    dataset = BenchmarkDataset(data_dir=args.data_dir)
    runner = BenchmarkRunner(
        dataset=dataset, 
        model=model, 
        output_dir=args.output_dir
    )
    
    # Run Benchmark
    logger.info(f"Starting Benchmark with model: {args.model} (Page-by-Page: {args.page_by_page}, Workers: {args.workers})")
    runner.run(
        system_instruction=SYSTEM_INSTRUCTION,
        prompt_template=PROMPT_TEMPLATE,
        page_by_page_prompt_template=PAGE_BY_PAGE_PROMPT_TEMPLATE,
        page_by_page=args.page_by_page,
        max_workers=args.workers
    )

if __name__ == "__main__":
    main()
