from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.reporting import write_json


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Snapshot a report directory into an immutable baseline bundle.")
    parser.add_argument("--reports", required=True, help="Existing reports directory.")
    parser.add_argument("--output", default="baselines", help="Baseline output root directory.")
    parser.add_argument("--name", help="Optional baseline snapshot name.")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / args.reports
    output_root = repo_root / args.output
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_name = args.name or f"baseline_{timestamp}"
    destination = output_root / snapshot_name
    if destination.exists():
        raise FileExistsError(f"Baseline snapshot already exists: {destination}")
    shutil.copytree(reports_dir, destination)

    benchmark_path = destination / "benchmark.json"
    ablation_path = destination / "ablation.json"
    determinism_path = destination / "determinism.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8")) if benchmark_path.exists() else {}
    ablation = json.loads(ablation_path.read_text(encoding="utf-8")) if ablation_path.exists() else {}
    determinism = json.loads(determinism_path.read_text(encoding="utf-8")) if determinism_path.exists() else {}
    baseline_name = ablation.get("baseline", "")
    baseline_rate = (
        ablation.get("variants", {}).get(baseline_name, {}).get("aggregate", {}).get("attempt_1_or_2_exact_rate")
    )
    full_rate = benchmark.get("aggregate", {}).get("attempt_1_or_2_exact_rate")
    lift = None
    if baseline_rate is not None and full_rate is not None:
        lift = full_rate - baseline_rate
    manifest = {
        "snapshot_name": snapshot_name,
        "source_reports_dir": str(reports_dir),
        "task_set_used": benchmark.get("split", "unknown"),
        "exact_rate": full_rate,
        "baseline_rate": baseline_rate,
        "lift": lift,
        "determinism_result": {
            "stable_outputs": determinism.get("stable_outputs"),
            "stable_rankings": determinism.get("stable_rankings"),
            "stable_metrics": determinism.get("stable_metrics"),
        },
        "report_generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(repo_root),
    }
    write_json(destination / "baseline_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
