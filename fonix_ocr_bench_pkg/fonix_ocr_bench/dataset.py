import json
import os
import pathlib
from typing import List, Dict, Tuple

class BenchmarkDataset:
    def __init__(self, data_dir: str):
        self.data_dir = pathlib.Path(data_dir)
        self.samples = self._load_samples()

    def _load_samples(self) -> List[Tuple[str, str, Dict]]:
        """
        Loads PDF and JSON pairs from the data directory.
        Returns a list of (pdf_path, json_path, ground_truth_json).
        """
        samples = []
        # Support both flat directory and nested 'all_together' if it exists inside data_dir
        search_dirs = [self.data_dir]
        if (self.data_dir / "all_together").exists():
             search_dirs.append(self.data_dir / "all_together")

        for d in search_dirs:
            for file in d.glob("*.pdf"):
                base_name = file.stem
                json_path = d / f"{base_name}.json"
                if json_path.exists():
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            gt = json.load(f)
                        samples.append((str(file), str(json_path), gt))
                    except json.JSONDecodeError as e:
                        error_msg = (
                            f"\n{'='*70}\n"
                            f"ERROR: Malformed JSON file detected!\n"
                            f"{'='*70}\n"
                            f"File: {json_path}\n"
                            f"Line: {e.lineno}, Column: {e.colno}\n"
                            f"Error: {e.msg}\n"
                            f"{'='*70}\n"
                            f"Please fix the JSON syntax error before running the benchmark.\n"
                            f"{'='*70}"
                        )
                        raise ValueError(error_msg) from e
        
        print(f"Loaded {len(samples)} samples from {self.data_dir}")
        if len(samples) == 0:
            print(f"WARNING: No PDF/JSON pairs found in {self.data_dir}")
            print(f"Searched in directories: {[str(d) for d in search_dirs]}")
        
        return samples

    def get_prompt_data(self, idx: int) -> Tuple[str, str, str]:
        """
        Returns (pdf_path, structure_injected, full_prompt) for a given index.
        """
        pdf_path, _, gt = self.samples[idx]
        structure_injected = self.create_structure_injected(gt)
        return pdf_path, structure_injected

    def create_structure_injected(self, answer_json: Dict) -> str:
        """
        Creates the STRUCTURE_INJECTED JSON string from the answer JSON.
        Removes 'crossedout_text' and empties values.
        """
        structure = self._clean_structure(answer_json)
        return json.dumps(structure, indent=4)

    def _clean_structure(self, data):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                if k == "crossedout_text":
                    continue
                
                # Special handling for student_answers to keep the structure but empty values
                if k == "answer" or k == "is_illigible":
                     new_data[k] = ""
                elif k == "paper_title":
                    new_data[k] = ""
                elif isinstance(v, (dict, list)):
                    new_data[k] = self._clean_structure(v)
                else:
                    # Keep other keys like 'test_number', 'instruction', 'question_type' as is?
                    # The user prompt example shows 'test_number', 'instruction', 'question_type' preserved with values.
                    # But "values of each key of the json should be empty but should specify the type of the value"
                    # User example:
                    # "test_number": "01",
                    # "instruction": "Fill in the blanks using the letters a-g.",
                    # "question_type": "Fill in the blanks",
                    # "student_answers": { "1": { "answer": "", "is_illigible": "" } ... }
                    
                    # So metadata keys are kept, student answer values are emptied.
                    # How to distinguish?
                    # The structure seems to depend on keys.
                    # 'paper_title' -> empty
                    # 'questions' -> list of dicts
                    # Inside question: 'test_number', 'instruction', 'question_type' -> KEEP VALUES?
                    # The user example CLEARLY keeps 'test_number', 'instruction', 'question_type'.
                    # It empties 'student_answers' values (answer, is_illigible) and 'paper_title'.
                    
                    new_data[k] = v
            return new_data
        elif isinstance(data, list):
            return [self._clean_structure(item) for item in data]
        else:
            return data

