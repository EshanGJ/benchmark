import json
import os
import pathlib
import datetime
import time
import re
import fitz  # PyMuPDF
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .dataset import BenchmarkDataset
from .model_interface import ModelInterface
from .evaluation import Evaluator
from .refinement import Refiner
from .report_generator import generate_html_report
from .logger import logger

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

    def _process_sample(self, 
                        sample: Tuple[str, str, Any], 
                        system_instruction: str, 
                        prompt_template: str, 
                        page_by_page: bool, 
                        page_by_page_prompt_template: Optional[str],
                        structures_dir: pathlib.Path,
                        run_dir: pathlib.Path) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        pdf_path, json_path, gt = sample
        pdf_name = pathlib.Path(pdf_path).name
        sample_prompt_tokens = 0
        sample_candidate_tokens = 0
        sample_thought_tokens = 0
        sample_cost = 0.0
        sample_recognition_time = 0.0
        
        logger.info(f"Processing {pdf_name} (Page-by-Page: {page_by_page})...")
        
        try:
            if page_by_page:
                # Page-by-Page Prediction
                doc = fitz.open(pdf_path)
                structure_injected = self.dataset.create_structure_injected(gt)
                current_json = structure_injected
                
                # Save structure
                with open(structures_dir / f"{pathlib.Path(pdf_name).stem}_structure.json", "w", encoding='utf-8') as f:
                    f.write(structure_injected)
                
                for page_index in range(len(doc)):
                    logger.info(f"Processing page {page_index + 1}/{len(doc)} of {pdf_name}...")
                    
                    # Render page to image bytes
                    page = doc.load_page(page_index)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Scale up for better OCR
                    image_bytes = pix.tobytes("png")
                    
                    prompt = page_by_page_prompt_template.replace("{PREVIOUS_JSON}", current_json)
                    
                    start_time = time.time()
                    prediction_result = self.model.call(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        image_bytes=image_bytes
                    )
                    sample_recognition_time += time.time() - start_time
                    
                    # Parse and update current_json
                    match = re.search(r'```json\s*(.*?)\s*```', prediction_result.text, re.DOTALL)
                    if match:
                        json_text = match.group(1)
                        current_json = json_text 
                    else:
                        current_json = prediction_result.text

                    # Track usage
                    u = prediction_result.usage
                    sample_prompt_tokens += u.prompt_token_count
                    sample_candidate_tokens += u.candidates_token_count
                    sample_thought_tokens += (u.thoughts_token_count if hasattr(u, 'thoughts_token_count') else 0)
                    
                    cost = self.model.calculate_cost(u)
                    sample_cost += cost
                    logger.debug(f"Page {page_index + 1} cost: ${cost:.6f} (Tokens: P:{u.prompt_token_count}, C:{u.candidates_token_count})")
                
                doc.close()
                pred_json = json.loads(current_json)
            else:
                # Full Paper Prediction (Original Logic)
                logger.info(f"Injecting JSON structure for {pdf_name} without values...")
                structure_injected = self.dataset.create_structure_injected(gt)
                
                # Save structure
                with open(structures_dir / f"{pathlib.Path(pdf_name).stem}_structure.json", "w", encoding='utf-8') as f:
                    f.write(structure_injected)

                prompt = prompt_template.replace("{STRUCTURE_INJECTED}", structure_injected)
                
                logger.info(f"Recognizing text using model...")
                start_time = time.time()
                prediction_result = self.model.call(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    image_path=pdf_path
                )
                sample_recognition_time = time.time() - start_time
                
                # Parse Prediction
                match = re.search(r'```json\s*(.*?)\s*```', prediction_result.text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                    pred_json = json.loads(json_text)
                else:
                    try:
                        pred_json = json.loads(prediction_result.text)
                    except:
                        logger.warning(f"Failed to parse JSON for {pdf_name}")
                        pred_json = {"error": "Failed to parse JSON", "raw": prediction_result.text}
                
                u = prediction_result.usage
                sample_prompt_tokens = u.prompt_token_count
                sample_candidate_tokens = u.candidates_token_count
                sample_thought_tokens = (u.thoughts_token_count if hasattr(u, 'thoughts_token_count') else 0)
                sample_cost = self.model.calculate_cost(u)
                logger.debug(f"Sample cost: ${sample_cost:.6f} (Tokens: P:{u.prompt_token_count}, C:{u.candidates_token_count})")
            
            # Evaluation
            logger.info(f"Evaluating results against ground truth for {pdf_name}...")
            eval_metrics = self.evaluator.calculate_hallucinations(gt, pred_json)
            
            # Refinement
            logger.info(f"Refining results with LLM for {pdf_name}...")
            refined_metrics = self.refiner.refine(eval_metrics)
            
            # Save individual result
            result_entry = {
                "pdf_name": pdf_name,
                "metrics": eval_metrics,
                "refined_metrics": refined_metrics,
                "usage": {
                    "prompt_tokens": sample_prompt_tokens,
                    "candidate_tokens": sample_candidate_tokens,
                    "thought_tokens": sample_thought_tokens
                },
                "cost": sample_cost,
                "recognition_time": sample_recognition_time,
                "prediction": pred_json
            }
            
            with open(run_dir / f"{pathlib.Path(pdf_name).stem}_result.json", "w", encoding='utf-8') as f:
                json.dump(result_entry, f, indent=4)
            
            summary_entry = {
                "pdf_name": pdf_name,
                "word_level_hallucination_rate": eval_metrics.get("word_level_hallucination_rate"),
                "refined_word_level_hallucination_rate": refined_metrics.get("word_level_hallucination_rate"),
                "fabricated_hallucination_rate": eval_metrics.get("fabricated_hallucination_rate"),
                "crossed_out_hallucination_rate": eval_metrics.get("crossed_out_hallucination_rate"),
                "illegibility_hallucination_rate": eval_metrics.get("illegibility_hallucination_rate"),
                "question_type_metrics": eval_metrics.get("question_type_metrics"),
                "refined_question_type_metrics": refined_metrics.get("question_type_metrics"),
                "cost": sample_cost,
                "recognition_time": sample_recognition_time
            }
            
            return result_entry, summary_entry

        except Exception as e:
            logger.error(f"Error processing {pdf_name}: {e}")
            with open(run_dir / f"{pathlib.Path(pdf_name).stem}_error.txt", "w", encoding='utf-8') as f:
                f.write(str(e))
            return None

    def run(self, 
            system_instruction: str, 
            prompt_template: str, 
            page_by_page: bool = False, 
            page_by_page_prompt_template: Optional[str] = None,
            max_workers: int = 4):
        """
        Runs the benchmark.
        
        Args:
            system_instruction (str): The system instruction for the model.
            prompt_template (str): The prompt template containing {STRUCTURE_INJECTED}.
            page_by_page (bool): Whether to process the PDF page by page.
            page_by_page_prompt_template (str): The prompt template for page-by-page processing.
            max_workers (int): Maximum number of concurrent workers.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        
        structures_dir = run_dir / "structures"
        structures_dir.mkdir(parents=True, exist_ok=True)
        
        summary_results = []
        detailed_results = []
        total_benchmark_cost = 0.0
        total_recognition_time = 0.0

        logger.info(f"Starting concurrent benchmark with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    self._process_sample, 
                    sample, 
                    system_instruction, 
                    prompt_template, 
                    page_by_page, 
                    page_by_page_prompt_template, 
                    structures_dir, 
                    run_dir
                ) for sample in self.dataset.samples
            ]
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    result_entry, summary_entry = result
                    detailed_results.append(result_entry)
                    summary_results.append(summary_entry)
                    total_benchmark_cost += result_entry["cost"]
                    total_recognition_time += result_entry["recognition_time"]

        # Aggregate question type metrics
        question_type_summary = {}
        refined_question_type_summary = {}
        
        for result in summary_results:
            # Original
            qtype_metrics = result.get("question_type_metrics", {})
            for qtype, metrics in qtype_metrics.items():
                if qtype not in question_type_summary:
                    question_type_summary[qtype] = {
                        "fabricated": 0, "crossed": 0, "illegible": 0, "gt_words": 0, "hallu_words": 0
                    }
                for field in ["fabricated", "crossed", "illegible", "gt_words", "hallu_words"]:
                    question_type_summary[qtype][field] += metrics.get(field, 0)
            
            # Refined
            ref_qtype_metrics = result.get("refined_question_type_metrics", {})
            for qtype, metrics in ref_qtype_metrics.items():
                if qtype not in refined_question_type_summary:
                    refined_question_type_summary[qtype] = {
                        "fabricated": 0, "crossed": 0, "illegible": 0, "gt_words": 0, "hallu_words": 0
                    }
                for field in ["fabricated", "crossed", "illegible", "gt_words", "hallu_words"]:
                    refined_question_type_summary[qtype][field] += metrics.get(field, 0)
        
        # Calculate rates for each summary
        for summary in [question_type_summary, refined_question_type_summary]:
            for qtype, metrics in summary.items():
                gt_words = metrics["gt_words"]
                metrics["hallucination_rate"] = metrics["hallu_words"] / gt_words if gt_words > 0 else 0
                metrics["fabricated_rate"] = metrics["fabricated"] / gt_words if gt_words > 0 else 0
                metrics["crossed_rate"] = metrics["crossed"] / gt_words if gt_words > 0 else 0
                metrics["illegible_rate"] = metrics["illegible"] / gt_words if gt_words > 0 else 0

        # Save Summary
        logger.info(f"Saving summary to {run_dir}/summary.json")
        summary_json = {
            "total_cost": total_benchmark_cost,
            "average_cost": total_benchmark_cost / len(self.dataset.samples) if self.dataset.samples else 0,
            "total_recognition_time": total_recognition_time,
            "average_recognition_time": total_recognition_time / len(self.dataset.samples) if self.dataset.samples else 0,
            "average_word_level_hallucination_rate": sum(r["word_level_hallucination_rate"] for r in summary_results) / len(summary_results) if summary_results else 0,
            "average_refined_word_level_hallucination_rate": sum(r["refined_word_level_hallucination_rate"] for r in summary_results) / len(summary_results) if summary_results else 0,
            "average_fabricated_hallucination_rate": sum(r["fabricated_hallucination_rate"] for r in summary_results) / len(summary_results) if summary_results else 0,
            "average_crossed_out_hallucination_rate": sum(r["crossed_out_hallucination_rate"] for r in summary_results) / len(summary_results) if summary_results else 0,
            "average_illegibility_hallucination_rate": sum(r["illegibility_hallucination_rate"] for r in summary_results) / len(summary_results) if summary_results else 0,
            "question_type_summary": question_type_summary,
            "refined_question_type_summary": refined_question_type_summary,
            "results": summary_results
        }
        with open(run_dir / "summary.json", "w", encoding='utf-8') as f:
            json.dump(summary_json, f, indent=4)
            
        # Generate HTML Report
        logger.info(f"Generating HTML report...")
        report_path = generate_html_report(summary_json, detailed_results, run_dir)
        logger.info(f"HTML report saved to {report_path}")
            
        logger.info(f"Benchmark completed. Results saved to {run_dir}")
        logger.info(f"Total Cost: ${total_benchmark_cost:.4f}")
