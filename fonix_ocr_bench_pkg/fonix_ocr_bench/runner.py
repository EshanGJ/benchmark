import json
import os
import pathlib
import datetime
from typing import Dict, Any, Optional
from .dataset import BenchmarkDataset
from .model_interface import ModelInterface
from .evaluation import Evaluator
from .refinement import Refiner

class BenchmarkRunner:
    def __init__(self, 
                 dataset: BenchmarkDataset, 
                 model: ModelInterface, 
                 output_dir: str = "results"):
        self.dataset = dataset
        self.model = model
        self.output_dir = pathlib.Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.evaluator = Evaluator()
        self.refiner = Refiner(model)

    def run(self, system_instruction: str, prompt_template: str):
        """
        Runs the benchmark.
        
        Args:
            system_instruction (str): The system instruction for the model.
            prompt_template (str): The prompt template containing {STRUCTURE_INJECTED}.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        
        summary_results = []
        total_cost = 0.0

        for i, sample in enumerate(self.dataset.samples):
            pdf_path, json_path, gt = sample
            pdf_name = pathlib.Path(pdf_path).name
            
            print(f"Processing {pdf_name}...")
            
            # Preparation
            structure_injected = self.dataset.create_structure_injected(gt)
            prompt = prompt_template.replace("{STRUCTURE_INJECTED}", structure_injected)
            
            # Prediction
            try:
                prediction_result = self.model.call(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    image_path=pdf_path
                )
                
                # Parse Prediction
                # Attempt to extract JSON
                import re
                match = re.search(r'```json\s*(.*?)\s*```', prediction_result.text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                    pred_json = json.loads(json_text)
                else:
                    # Fallback or raw
                    try:
                        pred_json = json.loads(prediction_result.text)
                    except:
                        print(f"Failed to parse JSON for {pdf_name}")
                        pred_json = {"error": "Failed to parse JSON", "raw": prediction_result.text}
                
                # Evaluation
                eval_metrics = self.evaluator.calculate_hallucinations(gt, pred_json)
                
                # Refinement
                refined_metrics = self.refiner.refine(eval_metrics)
                
                # Cost
                cost = self.model.calculate_cost(prediction_result.usage)
                total_cost += cost
                
                # Save individual result
                result_entry = {
                    "pdf_name": pdf_name,
                    "metrics": eval_metrics,
                    "refined_metrics": refined_metrics,
                    "cost": cost,
                    "prediction": pred_json
                }
                
                with open(run_dir / f"{pathlib.Path(pdf_name).stem}_result.json", "w", encoding='utf-8') as f:
                    json.dump(result_entry, f, indent=4)
                
                summary_results.append({
                    "pdf_name": pdf_name,
                    "word_level_hallucination_rate": eval_metrics.get("word_level_hallucination_rate"),
                    "refined_word_level_hallucination_rate": refined_metrics.get("word_level_hallucination_rate"),
                    "cost": cost
                })

            except Exception as e:
                print(f"Error processing {pdf_name}: {e}")
                # Log error
                with open(run_dir / f"{pathlib.Path(pdf_name).stem}_error.txt", "w", encoding='utf-8') as f:
                    f.write(str(e))

        # Save Summary
        with open(run_dir / "summary.json", "w", encoding='utf-8') as f:
            json.dump({
                "total_cost": total_cost,
                "results": summary_results
            }, f, indent=4)
            
        print(f"Benchmark completed. Results saved to {run_dir}")
        print(f"Total Cost: ${total_cost:.4f}")
