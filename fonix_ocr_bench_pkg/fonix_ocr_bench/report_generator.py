import os
import json
import datetime
import pathlib
from typing import List, Dict, Any

def generate_html_report(summary_data: Dict[str, Any], detailed_results: List[Dict[str, Any]], output_dir: pathlib.Path):
    """
    Generates a detailed HTML report for the benchmark results.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CSS for the report
    css = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 100%;
        margin: 0;
        padding: 20px;
        background-color: #f4f7f6;
        overflow-x: hidden;
    }
    .container {
        max-width: 1600px;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .summary-card {
        background: #fff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    .metric-item {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        text-align: center;
        border-left: 4px solid #3498db;
    }
    .metric-value {
        font-size: 1.3em;
        font-weight: bold;
        display: block;
        color: #34495e;
    }
    .metric-label {
        font-size: 0.8em;
        color: #7f8c8d;
        text-transform: uppercase;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        background: #fff;
        margin-bottom: 30px;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        table-layout: auto;
    }
    th, td {
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid #eee;
        font-size: 0.9em;
        word-break: break-all;
    }
    th {
        background-color: #3498db;
        color: white;
        text-transform: uppercase;
        font-size: 0.75em;
        letter-spacing: 0.05em;
    }
    tr:hover {
        background-color: #f9f9f9;
    }
    .rate-high { color: #e74c3c; font-weight: bold; }
    .rate-medium { color: #f39c12; font-weight: bold; }
    .rate-low { color: #27ae60; font-weight: bold; }
    
    .details-cell {
        max-width: 500px;
        min-width: 300px;
    }
    
    details {
        background: #f1f2f6;
        padding: 10px;
        border-radius: 4px;
        margin-top: 5px;
        width: 100%;
        box-sizing: border-box;
    }
    summary {
        cursor: pointer;
        font-weight: bold;
        outline: none;
    }
    .diff-table-container {
        overflow-x: auto;
        margin-top: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .diff-table {
        width: 100%;
        font-size: 0.9em;
        margin-bottom: 0;
        box-shadow: none;
        table-layout: fixed;
    }
    .diff-table th, .diff-table td {
        word-break: break-all;
        white-space: normal;
    }
    .diff-table th { background-color: #7f8c8d; }
    .gt-col { color: #2980b9; width: 40%;}
    .pred-col { color: #c0392b; width: 40%;}
    .q-col { width: 20%; }
    
    pre {
        background: #272822;
        color: #f8f8f2;
        padding: 10px;
        border-radius: 4px;
        overflow-x: auto;
        font-size: 0.85em;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    """

    def get_rate_class(rate):
        if rate is None: return ""
        if rate > 0.1: return "rate-high"
        if rate > 0.03: return "rate-medium"
        return "rate-low"

    # Summary Section
    summary_html = f"""
    <div class="summary-card">
        <h1>Benchmark Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <div class="metrics-grid">
            <div class="metric-item">
                <span class="metric-value">${summary_data.get('total_cost', 0):.4f}</span>
                <span class="metric-label">Total Cost</span>
            </div>
            <div class="metric-item">
                <span class="metric-value">${summary_data.get('average_cost', 0):.4f}</span>
                <span class="metric-label">Avg Cost</span>
            </div>
            <div class="metric-item" style="border-left-color: #9b59b6;">
                <span class="metric-value">{summary_data.get('total_recognition_time', 0):.2f}s</span>
                <span class="metric-label">Total Time</span>
            </div>
            <div class="metric-item" style="border-left-color: #9b59b6;">
                <span class="metric-value">{summary_data.get('average_recognition_time', 0):.2f}s</span>
                <span class="metric-label">Avg Time</span>
            </div>
            <div class="metric-item">
                <span class="metric-value {get_rate_class(summary_data.get('average_word_level_hallucination_rate', 0))}">{summary_data.get('average_word_level_hallucination_rate', 0)*100:.2f}%</span>
                <span class="metric-label">Avg Hallucination</span>
            </div>
            <div class="metric-item">
                <span class="metric-value {get_rate_class(summary_data.get('average_refined_word_level_hallucination_rate', 0))}">{summary_data.get('average_refined_word_level_hallucination_rate', 0)*100:.2f}%</span>
                <span class="metric-label">Avg Refined</span>
            </div>
            <div class="metric-item" style="border-left-color: #e67e22;">
                <span class="metric-value {get_rate_class(summary_data.get('average_fabricated_hallucination_rate', 0))}">{summary_data.get('average_fabricated_hallucination_rate', 0)*100:.2f}%</span>
                <span class="metric-label">Avg Fabricated</span>
            </div>
            <div class="metric-item" style="border-left-color: #e67e22;">
                <span class="metric-value {get_rate_class(summary_data.get('average_crossed_out_hallucination_rate', 0))}">{summary_data.get('average_crossed_out_hallucination_rate', 0)*100:.2f}%</span>
                <span class="metric-label">Avg Crossed-out</span>
            </div>
            <div class="metric-item" style="border-left-color: #e67e22;">
                <span class="metric-value {get_rate_class(summary_data.get('average_illegibility_hallucination_rate', 0))}">{summary_data.get('average_illegibility_hallucination_rate', 0)*100:.2f}%</span>
                <span class="metric-label">Avg Illegibility</span>
            </div>
        </div>
    </div>
    """

    # Detailed Results Table
    rows = []
    for res in detailed_results:
        metrics = res.get("metrics", {})
        refined = res.get("refined_metrics", {})
        pdf_name = res.get("pdf_name", "N/A")
        
        # Hallucination details
        replaced = metrics.get("replaced_word_pairs", [])
        inserted = metrics.get("inserted_words", [])
        
        hallucination_details = ""
        if replaced or inserted:
            hallucination_details = "<details><summary>View Details</summary>"
            if replaced:
                hallucination_details += "<h4>Replaced Words</h4><div class='diff-table-container'><table class='diff-table'><tr><th class='q-col'>Q</th><th class='gt-col'>GT</th><th class='pred-col'>Pred</th></tr>"
                for pair in replaced:
                    q = pair.get("question", "")
                    sub = pair.get("sub_question", "")
                    path = f"{q} ({sub})" if sub else q
                    hallucination_details += f"<tr><td class='q-col'>{path}</td><td class='gt-col'>{pair.get('gt_words')}</td><td class='pred-col'>{pair.get('pred_words')}</td></tr>"
                hallucination_details += "</table></div>"
            if inserted:
                hallucination_details += "<h4>Inserted Words</h4><ul>"
                for word in inserted:
                    hallucination_details += f"<li>{word.get('words')} (Q: {word.get('question')})</li>"
                hallucination_details += "</ul>"
            
            hallucination_details += "<h4>Raw Prediction</h4><pre><code>" + json.dumps(res.get("prediction"), indent=2) + "</code></pre>"
            hallucination_details += "</details>"

        rows.append(f"""
        <tr>
            <td><strong>{pdf_name}</strong></td>
            <td class="{get_rate_class(metrics.get('word_level_hallucination_rate', 0))}">{metrics.get('word_level_hallucination_rate', 0)*100:.2f}%</td>
            <td class="{get_rate_class(refined.get('word_level_hallucination_rate', 0))}">{refined.get('word_level_hallucination_rate', 0)*100:.2f}%</td>
            <td class="{get_rate_class(metrics.get('fabricated_hallucination_rate', 0))}">{metrics.get('fabricated_hallucination_rate', 0)*100:.2f}%</td>
            <td class="{get_rate_class(metrics.get('crossed_out_hallucination_rate', 0))}">{metrics.get('crossed_out_hallucination_rate', 0)*100:.2f}%</td>
            <td class="{get_rate_class(metrics.get('illegibility_hallucination_rate', 0))}">{metrics.get('illegibility_hallucination_rate', 0)*100:.2f}%</td>
            <td>${res.get('cost', 0):.4f}</td>
            <td>{res.get('recognition_time', 0):.2f}s</td>
            <td class="details-cell">{hallucination_details}</td>
        </tr>
        """)

    table_html = f"""
    <h2>Detailed Results</h2>
    <div style="overflow-x: auto;">
        <table>
            <thead>
                <tr>
                    <th>Sample</th>
                    <th>Hallu.</th>
                    <th>Refined</th>
                    <th>Fabri.</th>
                    <th>Cross.</th>
                    <th>Illeg.</th>
                    <th>Cost</th>
                    <th>Time</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OCR Benchmark Report</title>
        <style>
            {css}
        </style>
    </head>
    <body>
        <div class="container">
            {summary_html}
            {table_html}
        </div>
    </body>
    </html>
    """

    report_path = output_dir / "report.html"
    with open(report_path, "w", encoding='utf-8') as f:
        f.write(full_html)
    
    return report_path
