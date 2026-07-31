"""report.json generator (full raw data, machine-readable).

One element per scenario, containing the complete raw execution plan and all metrics.
Used for archiving.
"""

from __future__ import annotations

import json


def write_json_report(metrics_list: list[dict], output_path: str) -> None:
    """Write the metrics for all scenarios into report.json.

    Args:
        metrics_list: list of dicts returned by collect_scenario_metrics
        output_path: output file path
    """
    report = {
        "scenarios": metrics_list,
        "scenario_count": len(metrics_list),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
