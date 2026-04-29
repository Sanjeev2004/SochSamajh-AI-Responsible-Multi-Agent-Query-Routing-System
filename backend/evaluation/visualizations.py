from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bar_chart_svg(title: str, subtitle: str, rows: list[dict[str, Any]], metric_key: str) -> str:
    chart_rows = [row for row in rows if isinstance(row.get(metric_key), (float, int))]
    width = 920
    left = 220
    right = 40
    top = 90
    row_height = 54
    bar_height = 26
    chart_height = top + max(len(chart_rows), 1) * row_height + 40
    chart_width = width - left - right

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{chart_height}" viewBox="0 0 {width} {chart_height}">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="20" ry="20"/>',
        f'<text x="32" y="42" fill="#f8fafc" font-size="26" font-family="Arial, sans-serif" font-weight="700">{escape(title)}</text>',
        f'<text x="32" y="66" fill="#cbd5e1" font-size="14" font-family="Arial, sans-serif">{escape(subtitle)}</text>',
    ]

    for index, row in enumerate(chart_rows):
        y = top + index * row_height
        label = str(row.get("name", f"row_{index + 1}")).replace("_", " ")
        value = float(row[metric_key])
        bar_width = max(2.0, chart_width * max(0.0, min(1.0, value)))

        parts.extend(
            [
                f'<text x="32" y="{y + 18}" fill="#e2e8f0" font-size="14" font-family="Arial, sans-serif">{escape(label)}</text>',
                f'<rect x="{left}" y="{y}" width="{chart_width}" height="{bar_height}" rx="10" fill="#1e293b"/>',
                f'<rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" rx="10" fill="#14b8a6"/>',
                f'<text x="{left + chart_width + 8}" y="{y + 18}" fill="#f8fafc" font-size="13" font-family="Arial, sans-serif">{escape(_format_percent(value))}</text>',
            ]
        )

    parts.append("</svg>")
    return "".join(parts)


def _heatmap_svg(title: str, labels: list[str], matrix: dict[str, dict[str, int]]) -> str:
    width = 920
    height = 120 + 90 + len(labels) * 72
    cell_size = 72
    origin_x = 220
    origin_y = 120
    max_value = max((matrix.get(row, {}).get(col, 0) for row in labels for col in labels), default=1)

    def color(count: int) -> str:
        intensity = count / max_value if max_value else 0.0
        shade = int(235 - (intensity * 150))
        return f"rgb(15,{max(94, shade)},{max(110, shade)})"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0f172a" rx="20" ry="20"/>',
        f'<text x="32" y="42" fill="#f8fafc" font-size="26" font-family="Arial, sans-serif" font-weight="700">{escape(title)}</text>',
        '<text x="32" y="66" fill="#cbd5e1" font-size="14" font-family="Arial, sans-serif">Rows = expected labels, columns = predicted labels</text>',
    ]

    for col_index, label in enumerate(labels):
        x = origin_x + col_index * cell_size + cell_size / 2
        parts.append(
            f'<text x="{x}" y="{origin_y - 18}" fill="#e2e8f0" font-size="13" text-anchor="middle" font-family="Arial, sans-serif">{escape(label)}</text>'
        )

    for row_index, row_label in enumerate(labels):
        y = origin_y + row_index * cell_size
        parts.append(
            f'<text x="{origin_x - 16}" y="{y + 42}" fill="#e2e8f0" font-size="13" text-anchor="end" font-family="Arial, sans-serif">{escape(row_label)}</text>'
        )
        for col_index, col_label in enumerate(labels):
            x = origin_x + col_index * cell_size
            count = int(matrix.get(row_label, {}).get(col_label, 0))
            fill = color(count)
            text_fill = "#f8fafc" if count > max_value / 2 else "#e2e8f0"
            parts.extend(
                [
                    f'<rect x="{x}" y="{y}" width="{cell_size - 4}" height="{cell_size - 4}" rx="10" fill="{fill}" stroke="#334155" stroke-width="1"/>',
                    f'<text x="{x + (cell_size - 4) / 2}" y="{y + 40}" fill="{text_fill}" font-size="16" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700">{count}</text>',
                ]
            )

    parts.append("</svg>")
    return "".join(parts)


def _index_html(report: dict[str, Any], chart_files: dict[str, str]) -> str:
    benchmark_rows = report.get("benchmark_comparison", [])
    ablation_rows = report.get("ablation_comparison", [])
    summary = report.get("runs", {}).get("production", {}).get("summary", {})
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Evaluation Visual Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #020617; color: #e2e8f0; margin: 0; padding: 32px; }}
    h1, h2 {{ color: #f8fafc; }}
    .card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 18px; padding: 20px; margin-bottom: 24px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .stat {{ background: #111827; border-radius: 12px; padding: 14px; }}
    img {{ width: 100%; max-width: 920px; border-radius: 18px; border: 1px solid #1e293b; display: block; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #1e293b; }}
    th {{ color: #93c5fd; }}
  </style>
</head>
<body>
  <h1>Evaluation Visual Report</h1>
  <div class="card">
    <div class="stats">
      <div class="stat"><strong>Routing Accuracy</strong><br />{_format_percent(float(summary.get("routing_accuracy", 0.0)))}</div>
      <div class="stat"><strong>Risk Accuracy</strong><br />{_format_percent(float(summary.get("risk_accuracy", 0.0)))}</div>
      <div class="stat"><strong>Routing Macro F1</strong><br />{_format_percent(float(summary.get("routing_macro_f1", 0.0)))}</div>
      <div class="stat"><strong>P95 Latency</strong><br />{float(summary.get("latency_seconds", {}).get("p95_seconds", 0.0)):.2f}s</div>
    </div>
  </div>
  <div class="card"><h2>Benchmark Comparison</h2><img src="{escape(chart_files['benchmark'])}" alt="Benchmark comparison chart" /></div>
  <div class="card"><h2>Ablation Comparison</h2><img src="{escape(chart_files['ablation'])}" alt="Ablation comparison chart" /></div>
  <div class="card"><h2>Domain Confusion Matrix</h2><img src="{escape(chart_files['domain'])}" alt="Domain confusion matrix" /></div>
  <div class="card"><h2>Risk Confusion Matrix</h2><img src="{escape(chart_files['risk'])}" alt="Risk confusion matrix" /></div>
  <div class="card">
    <h2>Benchmark Table</h2>
    <table>
      <thead><tr><th>Name</th><th>Routing Accuracy</th><th>Risk Accuracy</th><th>High-Risk F1</th></tr></thead>
      <tbody>
        {"".join(f"<tr><td>{escape(str(row.get('name', 'unknown')))}</td><td>{escape(_format_percent(float(row.get('routing_accuracy', 0.0)))) if isinstance(row.get('routing_accuracy'), (float, int)) else escape(str(row.get('status', 'n/a')))}</td><td>{escape(_format_percent(float(row.get('risk_accuracy', 0.0)))) if isinstance(row.get('risk_accuracy'), (float, int)) else '-'}</td><td>{escape(_format_percent(float(row.get('high_risk_f1', 0.0)))) if isinstance(row.get('high_risk_f1'), (float, int)) else '-'}</td></tr>" for row in benchmark_rows)}
      </tbody>
    </table>
  </div>
  <div class="card">
    <h2>Ablation Table</h2>
    <table>
      <thead><tr><th>Name</th><th>Routing Accuracy</th><th>Risk Accuracy</th><th>High-Risk F1</th></tr></thead>
      <tbody>
        {"".join(f"<tr><td>{escape(str(row.get('name', 'unknown')))}</td><td>{escape(_format_percent(float(row.get('routing_accuracy', 0.0))))}</td><td>{escape(_format_percent(float(row.get('risk_accuracy', 0.0))))}</td><td>{escape(_format_percent(float(row.get('high_risk_f1', 0.0))))}</td></tr>" for row in ablation_rows)}
      </tbody>
    </table>
  </div>
</body>
</html>"""


def generate_visual_report(report: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    benchmark_svg = _bar_chart_svg(
        "Benchmark Comparison",
        "Production router vs baselines on routing accuracy",
        report.get("benchmark_comparison", []),
        "routing_accuracy",
    )
    ablation_svg = _bar_chart_svg(
        "Ablation Comparison",
        "Production vs disabled-component variants on routing accuracy",
        report.get("ablation_comparison", []),
        "routing_accuracy",
    )

    production_metrics = report.get("runs", {}).get("production", {}).get("metrics", {})
    domain_matrix = production_metrics.get("domain_confusion_matrix", {})
    risk_matrix = production_metrics.get("risk_confusion_matrix", {})

    benchmark_file = output_path / "benchmark_comparison.svg"
    ablation_file = output_path / "ablation_comparison.svg"
    domain_file = output_path / "domain_confusion_matrix.svg"
    risk_file = output_path / "risk_confusion_matrix.svg"
    index_file = output_path / "index.html"

    _write_text(benchmark_file, benchmark_svg)
    _write_text(ablation_file, ablation_svg)
    _write_text(domain_file, _heatmap_svg("Domain Confusion Matrix", ["medical", "legal", "general", "unknown"], domain_matrix))
    _write_text(risk_file, _heatmap_svg("Risk Confusion Matrix", ["low", "medium", "high"], risk_matrix))
    _write_text(
        index_file,
        _index_html(
            report,
            {
                "benchmark": benchmark_file.name,
                "ablation": ablation_file.name,
                "domain": domain_file.name,
                "risk": risk_file.name,
            },
        ),
    )

    return {
        "index_html": str(index_file),
        "benchmark_chart": str(benchmark_file),
        "ablation_chart": str(ablation_file),
        "domain_confusion_chart": str(domain_file),
        "risk_confusion_chart": str(risk_file),
    }
