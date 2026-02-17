import os
import pathlib
import json
from fonix_ocr_bench.report_generator import generate_html_report

def test_report():
    mock_summary = {
        "total_cost": 0.052,
        "average_cost": 0.026,
        "total_recognition_time": 45.5,
        "average_recognition_time": 22.75,
        "average_word_level_hallucination_rate": 0.045,
        "average_refined_word_level_hallucination_rate": 0.038,
        "average_fabricated_hallucination_rate": 0.015,
        "average_crossed_out_hallucination_rate": 0.005,
        "average_illegibility_hallucination_rate": 0.008,
        "results": [] 
    }
    
    mock_detailed = [
        {
            "pdf_name": "sample1.pdf",
            "metrics": {
                "word_level_hallucination_rate": 0.01,
                "fabricated_hallucination_rate": 0.005,
                "crossed_out_hallucination_rate": 0.0,
                "illegibility_hallucination_rate": 0.002,
                "replaced_word_pairs": [],
                "inserted_words": []
            },
            "refined_metrics": {
                "word_level_hallucination_rate": 0.005
            },
            "cost": 0.012,
            "recognition_time": 10.2,
            "prediction": {"text": "Clean prediction"}
        },
        {
            "pdf_name": "sample2.pdf",
            "metrics": {
                "word_level_hallucination_rate": 0.15,
                "fabricated_hallucination_rate": 0.08,
                "crossed_out_hallucination_rate": 0.04,
                "illegibility_hallucination_rate": 0.03,
                "replaced_word_pairs": [
                    {"question": "Q1", "gt_words": "apple", "pred_words": "apply"}
                ],
                "inserted_words": []
            },
            "refined_metrics": {
                "word_level_hallucination_rate": 0.12
            },
            "cost": 0.040,
            "recognition_time": 35.3,
            "prediction": {"text": "Noisy prediction"}
        }
    ]
    
    output_dir = pathlib.Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    report_path = generate_html_report(mock_summary, mock_detailed, output_dir)
    print(f"Report generated at: {report_path}")
    
    if report_path.exists():
        print("SUCCESS: report.html exists.")
        with open(report_path, "r", encoding='utf-8') as f:
            content = f.read()
            # Check for new metric columns/labels
            checks = [
                "Avg Cost", "Avg Fabricated", "Avg Crossed-out", "Avg Illegibility",
                "Fabricated", "Crossed-out", "Illegibility", # Table headers
                "0.0260" # Avg cost value
            ]
            for check in checks:
                if check in content:
                    print(f"SUCCESS: Found '{check}' in report.")
                else:
                    print(f"FAILURE: Missing '{check}' in report.")
    else:
        print("FAILURE: report.html not found.")

if __name__ == "__main__":
    test_report()
