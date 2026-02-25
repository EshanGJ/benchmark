# fonix_ocr_bench

A Python package and benchmarking suite for evaluating OCR models on handwritten text recognition and structured form extraction.

This repository contains the `fonix_ocr_bench` package and scripts to run standardized benchmarks using Google Gemini and other vision models to extract and evaluate handwritten student answers from exam or form images.

## Overview

The benchmarking suite enables:
- **OCR Evaluation**: Assess how well vision models extract handwritten text from scanned documents
- **Structured Data Extraction**: Extract answers from forms with various question types (fill-in-the-blank, underline, writing, Q&A, etc.)
- **Multi-Model Comparison**: Run benchmarks against different vision models (Gemini, GPT-4 Vision, custom models)
- **Detailed Reporting**: Generate comprehensive reports with accuracy metrics, cost analysis, and performance insights

## Directory Structure

- **`fonix_ocr_bench_pkg/`**: Core Python package source code
  - `cli.py`: Command-line interface
  - `dataset.py`: Dataset handling and parsing
  - `evaluation.py`: Metrics calculation and evaluation logic
  - `gemini3_model.py`: Google Gemini 3 model implementation
  - `model_interface.py`: Abstract base class for custom models
  - `report_generator.py`: HTML report generation
  - `runner.py`: Main benchmark runner
  - `utils.py`: Utility functions
- **`data/`**: Dataset directory containing PDF images and corresponding ground truth JSON files
- **`results/`**: Output directory for benchmark reports (timestamped subdirectories)
- **`run_benchmark.py`**: Main execution script to run benchmarks
- **`question_types.json`**: Configuration mapping question types to test numbers
- **`update_question_types.py`**: Utility script to update question types in data files
- **`consolidate_data.py`**: Utility script to consolidate data from multiple directories

## Setup

### 1. Environment Setup
Install miniconda in your system and then create and activate the conda environment:
```bash
conda create -n ocr-bench python=3.13

conda activate 
```

### 2. Install Package
Install the package in editable mode to enable imports:
```bash
cd fonix_ocr_bench_pkg
pip install -e .
cd ..
```
This installs dependencies including `google-genai`.

### 3. API Key Configuration
Set your Google API Key:
```bash
# Linux/Mac
export GOOGLE_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set GOOGLE_API_KEY=your_api_key_here
```

## Dataset Preparation Guide

### Directory Structure

Organize your data in a directory with paired PDF and JSON files:

```
data/
├── set_1_1.pdf       # Scanned image of a form/exam
├── set_1_1.json      # Ground truth answers for set_1_1.pdf
├── set_1_2.pdf
├── set_1_2.json
├── set_2_1.pdf
├── set_2_1.json
└── ...
```

### File Naming Convention

Use the naming pattern: `set_{SET_NUMBER}_{PAPER_NUMBER}.{ext}`

Example:
- `set_1_1.json` and `set_1_1.pdf` (Set 1, Paper 1)
- `set_2_3.json` and `set_2_3.pdf` (Set 2, Paper 3)

### PDF Files

- **Format**: Scanned or photographed images of exam papers/forms
- **Supported formats**: PDF
- **Content**: Handwritten student responses to various question types

### JSON Structure

Each JSON file contains the ground truth answers for a corresponding PDF. The structure is as follows:

```json
{
  "paper_title": "First term Evaluation -2018",
  "questions": [
    // if a question have only one answer
    {
      "test_number": "08",
      "instruction": "write on following topics",
      "question_type": "W",
      "student_answers": {
        "answer": "The person I admire in my life is my father...",
        "crossedout_text": [],
        "is_legible": "true"
      }
    },
    // answers for normal questions -> sub questions level 1
    {
      "test_number": "02",
      "instruction": "Underline the correct answer",
      "question_type": "U",
      "student_answers": {
        "1": {
          "answer": "didn't",
          "crossedout_text": [],
          "is_legible": "true"
        }
      }
    },
    // answers for nested questions -> level 2 sub questions
    {
      "test_number": "01",
      "instruction": "Fill in the blanks",
      "question_type": "FITB",
      "student_answers": {
        "1": {
            "1": {
                "answer": "d",
                "crossedout_text": [],
                "is_legible": "true"
            },
            "2": {
                "answer": "d",
                "crossedout_text": [],
                "is_legible": "true"
            },
        },
        "2": {
            "answer": "f",
            "crossedout_text": [],
            "is_legible": "true"
        }
      }
    }
  ]
}
```

**Source:** Real example from [set_1_1.json](data/set_1_1.json) - 11 questions (482 lines)

#### JSON Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `paper_title` | string | Title or identifier of the exam/form (e.g., "First term Evaluation -2018") |
| `questions` | array | Array of question objects |
| `test_number` | string | Question identifier (e.g., "01", "02", "09") |
| `instruction` | string | Instructions shown for this question (e.g., "Fill in the blanks", "Underline the correct answer") |
| `question_type` | string | Type of question (FITB, U, W, QA, C, or M) |
| `student_answers` | object/string | Answers indexed by sub-question number (for FITB, U, QA) or single object (for W) |
| `answer` | string | The handwritten answer text (e.g., "d", "heritage club", "flying rockets") |
| `crossedout_text` | array | Array of text that was crossed out and not rewritten (typically empty unless showing erasure) |
| `is_legible` | string | "true" if answer is legible/readable, "false" if illegible, empty string "" if unanswered |

### Question Types

The benchmark supports the following question types:

| Code | Type | Description | Example Structure |
|------|------|-------------|-------------------|
| **FITB** | Fill in the Blank | Multiple blanks to fill with words/letters (indexed answers) | `{"1": {"answer": "d"}, "2": {"answer": "f"}, ...}` |
| **U** | Underline | Select/underline correct option(s) from choices | `{"1": {"answer": "didn't"}, "2": {"answer": "immediate"}}` |
| **W** | Writing | Long-form written response (essay/paragraph) | `{"answer": "The person admire in my life is my lovely father..."}` |
| **QA** | Question & Answer | Multiple Q&A pairs with indexed answers | `{"1": {"answer": "flying rockets"}, "2": {"answer": "Mrs. Brown"}}` |
| **C** | Circling | Circling the relevant answer instead of underlining | `{"1": {"answer": "value"}}` |
| **M** | Matching | Match items from two sides by drawing lines | `{"1": {"answer": "matched_item"}}` |

### Question Type Mapping (question_types.json|optional)

The `question_types.json` file maps which test numbers correspond to each question type. This is used by the `update_question_types.py` script to automatically populate the `question_type` field.

```json
{
  "data": [
    {
      "question_type": "FITB",
      "sets": {
        "Set 1": [1, 4, 11, 3, 5],
        "Set 2": [3, 10, 11, 12, 1, 2, 5]
      }
    },
    {
      "question_type": "U",
      "sets": {
        "Set 1": [2, 9],
        "Set 2": [4, 7]
      }
    },
    {
      "major_question_type": "W",
      "sets": {
        "Set 1": [6, 8, 10, 14]
      }
    }
  ]
}
```

### Preparing Data Files

1. **Create JSON files**: Manually create or extract ground truth answers into JSON files following the structure [above](#json-structure)
2. **Organize with PDFs**: Place JSON files alongside their corresponding PDF files
3. **Update question types** (optional):
   ```bash
   python update_question_types.py
   ```
   This script automatically updates `question_type` fields in your JSON files based on `question_types.json` mappings

4. **Consolidate data** (if using multiple directories):
   ```bash
   python consolidate_data.py
   ```
   This copies files from a test directory structure into a single `data/all_together` directory with standardized naming

## Usage

### Option 1: Python Script (Recommended)
Run the benchmark script from the root directory:

```bash
python run_benchmark.py --data_dir "./data" --output_dir ./results --model gemini-3-flash-preview
```

### Option 2: Command Line Interface (CLI)
Once installed, you can also use the CLI command:

```bash
fonix-ocr-bench --data_dir "./data" --output_dir ./results --model gemini-3-flash-preview
```

### Arguments
- `--data_dir`: Directory containing PDF/JSON pairs (default: `./data`)
- `--output_dir`: Directory to save results (default: `./results`)
- `--model`: Model name to use for OCR (default: `gemini-3-flash-preview`, `gemini-3.1-pro-preview` also compatible. To add other models, need [advanced usage](#advanced-usage))

### Output
The benchmark generates:
- **`report.html`**: Visual HTML report with results and metrics
- **`{set_name}_result.json`**: Detailed results for each paper
- **`summary.json`**: Overall benchmark summary
- **`structures/`**: Extracted JSON structures programmatically

## Advanced Usage

### Custom Models

You can integrate custom vision models by creating a class that inherits from `ModelInterface`. See [GUIDE.md](fonix_ocr_bench_pkg/GUIDE.md) for detailed examples including OpenAI GPT and custom implementations.
