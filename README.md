# fonix_ocr_bench

A Python package and benchmarking suite for evaluating OCR models on handwritten text.

This repository contains the `fonix_ocr_bench` package and scripts to run standardized benchmarks using Google Gemini and other models.

## Directory Structure

- **`fonix_ocr_bench_pkg/`**: The core Python package source code.
- **`data/`**: Dataset directory containing PDFs and corresponding ground truth JSONs.
- **`results/`**: Output directory for benchmark reports.
- **`run_benchmark.py`**: Main execution script.

## Setup

1.  **Environment**:
    Activate your conda environment:
    ```bash
    conda activate eng
    ```

2.  **Install Package**:
    Install the package in editable mode to enable imports:
    ```bash
    cd fonix_ocr_bench_pkg
    pip install -e .
    cd ..
    ```
    *This installs dependencies including `google-genai`.*

3.  **API Key**:
    Set your Google API Key:
    ```bash
    # Linux/Mac
    export GOOGLE_API_KEY=your_api_key_here
    # Windows
    set GOOGLE_API_KEY=your_api_key_here
    ```

## Usage

### Option 1: Python Script (Recommended)
Run the benchmark script from the root directory:

```bash
python run_benchmark.py --data_dir "./data/all_together" --output_dir ./results
```

### Option 2: Command Line Interface (CLI)
Once installed, you can also use the CLI command:

```bash
fonix-ocr-bench --data_dir "./data/all_together" --output_dir ./results
```

### Arguments
- `--data_dir`: Directory containing PDF/JSON pairs (default: `./data/all_together`)
- `--output_dir`: Directory to save results (default: `./results`)
- `--model`: Model name (default: `gemini-3-flash-preview`)

## Documentation

For detailed guides on adding custom models, implementing cost functions, and understanding the metrics, see [GUIDE.md](fonix_ocr_bench_pkg/GUIDE.md).
