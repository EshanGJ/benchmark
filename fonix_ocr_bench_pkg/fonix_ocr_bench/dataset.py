import json
import os
import pathlib
from typing import List, Dict, Tuple
from .logger import logger

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
                        logger.error(f"Malformed JSON in {json_path}")
                        raise ValueError(error_msg) from e
        
        logger.info(f"Loaded {len(samples)} samples from {self.data_dir}")
        if len(samples) == 0:
            logger.warning(f"No PDF/JSON pairs found in {self.data_dir}")
            logger.debug(f"Searched in directories: {[str(d) for d in search_dirs]}")
        
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
                    new_data[k] = v
            return new_data
        elif isinstance(data, list):
            return [self._clean_structure(item) for item in data]
        else:
            return data
