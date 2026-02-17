import os
import json
import datetime
import pathlib
from typing import List, Dict, Any

def generate_html_report(summary_data: Dict[str, Any], detailed_results: List[Dict[str, Any]], output_dir: pathlib.Path):
    """
    Generates a professional dashboard HTML report for the benchmark results.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Icons (SVGs)
    icons = {
        "cost": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
        "time": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
        "hallucination": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
        "sample": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
    }

    # CSS for the dashboard
    css = """
    :root {
        --primary: #2563eb;
        --primary-light: #dbeafe;
        --secondary: #64748b;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg: #f8fafc;
        --card-bg: #ffffff;
        --text-main: #1e293b;
        --text-muted: #64748b;
        --border: #e2e8f0;
    }

    * { box-sizing: border-box; }
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: var(--bg);
        color: var(--text-main);
        margin: 0;
        padding: 0;
        line-height: 1.5;
    }
    .header {
        background: white;
        padding: 2rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }
    .header h1 { margin: 0; font-size: 1.875rem; font-weight: 700; color: var(--text-main); }
    .header p { margin: 0.5rem 0 0; color: var(--text-muted); font-size: 0.875rem; }

    .container { max-width: 1400px; margin: 0 auto; padding: 0 2rem 4rem; }

    .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    
    .stat-card {
        background: var(--card-bg);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }
    .stat-icon {
        width: 3rem;
        height: 3rem;
        border-radius: 0.75rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
    }
    .stat-icon.blue { background: var(--primary); }
    .stat-icon.green { background: var(--success); }
    .stat-icon.orange { background: var(--warning); }
    .stat-icon.red { background: var(--danger); }
    .stat-icon.purple { background: #8b5cf6; }

    .stat-info { display: flex; flex-direction: column; }
    .stat-label { font-size: 0.875rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.025em; }
    .stat-value { font-size: 1.5rem; font-weight: 700; color: var(--text-main); }

    .dashboard-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
    .card { background: var(--card-bg); border-radius: 1rem; border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .card-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
    .card-title { font-size: 1.125rem; font-weight: 600; margin: 0; }
    .card-body { padding: 1.5rem; }

    .chart-container { position: relative; height: 300px; width: 100%; }

    table { width: 100%; border-collapse: separate; border-spacing: 0; }
    th { background: #f1f5f9; padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
    td { padding: 1rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background-color: #f8fafc; }

    .badge { padding: 0.25rem 0.625rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; display: inline-flex; align-items: center; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-warning { background: #fef9c3; color: #854d0e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .badge-neutral { background: #f1f5f9; color: #475569; }

    .progress-bar-container { width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 4px; }
    .progress-bar { height: 100%; border-radius: 4px; transition: width 0.3s ease; }

    details { margin-top: 0.5rem; }
    summary { font-size: 0.875rem; color: var(--primary); cursor: pointer; font-weight: 500; }
    summary:hover { text-decoration: underline; }
    
    .diff-list { font-size: 0.875rem; margin-top: 0.75rem; }
    .diff-item { background: #f8fafc; border-radius: 0.5rem; padding: 0.75rem; margin-bottom: 0.5rem; border-left: 3px solid var(--primary); }
    .diff-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem; }
    .diff-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; margin-bottom: 0.25rem; }
    .diff-val { font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 0.8125rem; word-break: break-all; }
    .val-gt { color: #059669; }
    .val-pred { color: #dc2626; }

    pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; font-size: 0.75rem; }

    @media (max-width: 1024px) {
        .dashboard-layout { grid-template-columns: 1fr; }
    }
    """

    def get_status_props(rate):
        if rate is None: return "badge-neutral", "#94a3b8"
        if rate > 0.1: return "badge-danger", "#ef4444"
        if rate > 0.03: return "badge-warning", "#f59e0b"
        return "badge-success", "#22c55e"

    # Question Type Labels
    qtype_labels = {
        "QA": "Question Answering",
        "FITB": "Fill In The Blanks",
        "W": "Writing/Essay",
        "U": "Underline",
        "C": "Circling",
        "M": "Matching"
    }

    def generate_qtype_rows(qtype_summary, refined_qtype_summary):
        rows = ""
        # Use refined as the source of truth for qtypes
        for qtype, metrics in refined_qtype_summary.items():
            label = qtype_labels.get(qtype, qtype)
            hr = metrics.get('hallucination_rate', 0) * 100
            orig_hr = qtype_summary.get(qtype, {}).get('hallucination_rate', 0) * 100
            
            badge_cls, _ = get_status_props(metrics.get('hallucination_rate', 0))
            rows += f"""
            <tr>
                <td><strong>{label}</strong> <small style="color: var(--text-muted)">({qtype})</small></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="badge {badge_cls}">{hr:.1f}%</span>
                        <small style="color: var(--text-muted); text-decoration: line-through;">{orig_hr:.1f}%</small>
                    </div>
                </td>
                <td>{metrics.get('fabricated', 0)} ({metrics.get('fabricated_rate', 0)*100:.1f}%)</td>
                <td>{metrics.get('crossed', 0)} ({metrics.get('crossed_rate', 0)*100:.1f}%)</td>
                <td>{metrics.get('illegible', 0)} ({metrics.get('illegible_rate', 0)*100:.1f}%)</td>
                <td>{metrics.get('gt_words', 0)}</td>
            </tr>
            """
        return rows

    # Prepare data for charts
    chart_labels = [res.get("pdf_name", "N/A") for res in detailed_results]
    chart_hallu_data = [res.get("metrics", {}).get("word_level_hallucination_rate", 0) * 100 for res in detailed_results]
    chart_cost_data = [res.get("cost", 0) for res in detailed_results]
    chart_time_data = [res.get("recognition_time", 0) for res in detailed_results]

    qtype_summary = summary_data.get('question_type_summary', {})
    refined_qtype_summary = summary_data.get('refined_question_type_summary', {})
    
    chart_qtype_labels = [qtype_labels.get(qt, qt) for qt in refined_qtype_summary.keys()]
    chart_qtype_data = [m.get('hallucination_rate', 0) * 100 for m in refined_qtype_summary.values()]
    chart_qtype_orig_data = [qtype_summary.get(qt, {}).get('hallucination_rate', 0) * 100 for qt in refined_qtype_summary.keys()]

    summary_html = f"""
    <div class="header">
        <h1>OCR Benchmark Dashboard</h1>
        <p>Execution Summary • <strong>{timestamp}</strong></p>
    </div>

    <div class="container">
        <div class="grid-4" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));">
            <div class="stat-card">
                <div class="stat-icon blue">{icons['cost']}</div>
                <div class="stat-info">
                    <span class="stat-label">Total Cost</span>
                    <span class="stat-value">${summary_data.get('total_cost', 0):.3f}</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon blue" style="background: var(--secondary)">{icons['cost']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Cost</span>
                    <span class="stat-value">${summary_data.get('average_cost', 0):.4f}</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon purple">{icons['time']}</div>
                <div class="stat-info">
                    <span class="stat-label">Total Time</span>
                    <span class="stat-value">{summary_data.get('total_recognition_time', 0):.1f}s</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon purple" style="background: var(--secondary)">{icons['time']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Time</span>
                    <span class="stat-value">{summary_data.get('average_recognition_time', 0):.2f}s</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon orange">{icons['hallucination']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Hallucination</span>
                    <span class="stat-value">{summary_data.get('average_word_level_hallucination_rate', 0)*100:.2f}%</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon orange" style="background: var(--primary)">{icons['hallucination']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Refined</span>
                    <span class="stat-value">{summary_data.get('average_refined_word_level_hallucination_rate', 0)*100:.2f}%</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon red">{icons['hallucination']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Fabricated</span>
                    <span class="stat-value">{summary_data.get('average_fabricated_hallucination_rate', 0)*100:.2f}%</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon green">{icons['hallucination']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Crossed-out</span>
                    <span class="stat-value">{summary_data.get('average_crossed_out_hallucination_rate', 0)*100:.2f}%</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon orange" style="background: #e67e22;">{icons['hallucination']}</div>
                <div class="stat-info">
                    <span class="stat-label">Avg Illegibility</span>
                    <span class="stat-value">{summary_data.get('average_illegibility_hallucination_rate', 0)*100:.2f}%</span>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon green" style="background: #a855f7;">{icons['sample']}</div>
                <div class="stat-info">
                    <span class="stat-label">Samples Tested</span>
                    <span class="stat-value">{len(detailed_results)}</span>
                </div>
            </div>
        </div>

        <div class="dashboard-layout">
            <div class="card">
                <div class="card-header"><h3 class="card-title">Hallucination Rates per Sample (%)</h3></div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="halluChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3 class="card-title">Performance by Question Type (%)</h3></div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="qtypeChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3 class="card-title">Cost vs Speed Distribution</h3></div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="scatterChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 2rem;">
            <div class="card-header"><h3 class="card-title">Question Type Breakdown</h3></div>
            <div class="card-body" style="padding: 0;">
                <table>
                    <thead>
                        <tr>
                            <th>Question Type</th>
                            <th>Hallucination Rate</th>
                            <th>Fabricated</th>
                            <th>Crossed-out</th>
                            <th>Illegibility</th>
                            <th>GT Words</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_qtype_rows(summary_data.get('question_type_summary', {}), summary_data.get('refined_question_type_summary', {}))}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3 class="card-title">Detailed Execution Results</h3></div>
            <div class="card-body" style="padding: 0;">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 250px">Sample</th>
                            <th>Hallucination Metrics</th>
                            <th style="width: 150px">Efficiency</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for res in detailed_results:
        metrics = res.get("metrics", {})
        refined = res.get("refined_metrics", {})
        pdf_name = res.get("pdf_name", "N/A")
        
        # Prioritize refined rate for status
        main_rate = refined.get('word_level_hallucination_rate', 0)
        orig_rate = metrics.get('word_level_hallucination_rate', 0)
        
        badge_cls, bar_color = get_status_props(main_rate)
        
        # Hallucination details
        replaced = metrics.get("replaced_word_pairs", [])
        inserted = metrics.get("inserted_words", [])
        
        hallucination_details = ""
        if replaced or inserted:
            hallucination_details = "<details><summary>Review Discrepancies</summary><div class='diff-list'>"
            if replaced:
                for pair in replaced:
                    q = pair.get("question", "")
                    sub = pair.get("sub_question", "")
                    label = f"Ref: {q} ({sub})" if sub else f"Ref: {q}"
                    hallucination_details += f"""
                    <div class="diff-item">
                        <div style="font-weight: 600; margin-bottom: 4px;">Word Mismatch</div>
                        <div class="diff-grid">
                            <div><div class="diff-label">EXPECTED (GT)</div><div class="diff-val val-gt">{pair.get('gt_words')}</div></div>
                            <div><div class="diff-label">PREDICTED</div><div class="diff-val val-pred">{pair.get('pred_words')}</div></div>
                        </div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">{label}</div>
                    </div>"""
            if inserted:
                for word in inserted:
                    hallucination_details += f"""
                    <div class="diff-item" style="border-left-color: #f59e0b;">
                        <div style="font-weight: 600; margin-bottom: 4px;">Unexpected Insertion</div>
                        <div class="diff-val val-pred">{word.get('words')}</div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">Ref: {word.get('question')}</div>
                    </div>"""
            
            hallucination_details += "<h4 style='font-size: 0.875rem'>Raw Output</h4><pre><code>" + json.dumps(res.get("prediction"), indent=2) + "</code></pre>"
            hallucination_details += "</div></details>"

        summary_html += f"""
        <tr>
            <td>
                <div style="font-weight: 600;">{pdf_name}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Original: {orig_rate*100:.1f}%</div>
            </td>
            <td>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span class="badge {badge_cls}">{main_rate*100:.1f}%</span>
                    <div class="progress-bar-container" style="flex: 1">
                        <div class="progress-bar" style="width: {min(main_rate*100, 100)}%; background: {bar_color}"></div>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; color: #64748b;">
                    <span>Fab: {metrics.get('fabricated_hallucination_rate', 0)*100:.1f}%</span>
                    <span>Cross: {metrics.get('crossed_out_hallucination_rate', 0)*100:.1f}%</span>
                    <span>Illeg: {metrics.get('illegibility_hallucination_rate', 0)*100:.1f}%</span>
                </div>
            </td>
            <td>
                <div style="font-weight: 600;">${res.get('cost', 0):.4f}</div>
                <div style="font-size: 0.75rem; color: #64748b;">{res.get('recognition_time', 0):.2f}s</div>
            </td>
            <td>{hallucination_details}</td>
        </tr>
        """

    summary_html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OCR Benchmark Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            {css}
        </style>
    </head>
    <body>
        <div id="dashboard-root">
            {summary_html}
        </div>

        <script>
            // Hallucination Bar Chart
            const ctxHallu = document.getElementById('halluChart').getContext('2d');
            new Chart(ctxHallu, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(chart_labels)},
                    datasets: [
                        {{
                            label: 'Refined Rate (%)',
                            data: {json.dumps([res.get("refined_metrics", {}).get("word_level_hallucination_rate", 0) * 100 for res in detailed_results])},
                            backgroundColor: '#3b82f6',
                            borderRadius: 6
                        }},
                        {{
                            label: 'Original Rate (%)',
                            data: {json.dumps(chart_hallu_data)},
                            backgroundColor: '#94a3b8',
                            borderRadius: 6,
                            hidden: true
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: true, position: 'top' }} }},
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ borderDash: [5, 5] }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Question Type Bar Chart
            const ctxQType = document.getElementById('qtypeChart').getContext('2d');
            new Chart(ctxQType, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(chart_qtype_labels)},
                    datasets: [
                        {{
                            label: 'Refined Rate (%)',
                            data: {json.dumps(chart_qtype_data)},
                            backgroundColor: '#10b981',
                            borderRadius: 6
                        }},
                        {{
                            label: 'Original Rate (%)',
                            data: {json.dumps(chart_qtype_orig_data)},
                            backgroundColor: '#94a3b8',
                            borderRadius: 6,
                            hidden: true
                        }}
                    ]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: true, position: 'top' }} }},
                    scales: {{
                        x: {{ beginAtZero: true, grid: {{ borderDash: [5, 5] }} }},
                        y: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Scatter Chart (Cost vs Time)
            const ctxScatter = document.getElementById('scatterChart').getContext('2d');
            new Chart(ctxScatter, {{
                type: 'scatter',
                data: {{
                    datasets: [{{
                        label: 'Samples',
                        data: {json.dumps([{'x': t, 'y': c} for t, c in zip(chart_time_data, chart_cost_data)])},
                        backgroundColor: '#8b5cf6',
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Recognition Time (s)' }}, grid: {{ borderDash: [5, 5] }} }},
                        y: {{ title: {{ display: true, text: 'Cost ($)' }}, grid: {{ borderDash: [5, 5] }} }}
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                label: (context) => {{
                                    const names = {json.dumps(chart_labels)};
                                    return names[context.dataIndex] + ': ' + context.parsed.x + 's, $' + context.parsed.y;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    report_path = output_dir / "report.html"
    with open(report_path, "w", encoding='utf-8') as f:
        f.write(full_html)
    
    return report_path
