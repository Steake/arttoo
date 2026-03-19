from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.fixtures import discover_splits
from arc_epistemic.eval.reporting import multi_split_summary_markdown, next_stage_summary_markdown, write_json


def _run(command: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _split_output_dir(reports_dir: Path, split: str) -> Path:
    return reports_dir if split == "all" else reports_dir / split


def _bench_suite(repo_root: Path, reports_dir: Path, tasks: str, split: str) -> dict[str, dict[str, object]]:
    split_dir = _split_output_dir(reports_dir, split)
    split_dir.mkdir(parents=True, exist_ok=True)
    benchmark_json = split_dir / "benchmark.json"
    ablation_json = split_dir / "ablation.json"
    determinism_json = split_dir / "determinism.json"
    failures_json = split_dir / "failures.json"
    scorecard_json = split_dir / "scorecard.json"
    return {
        "benchmark": _run(
            ["python", "tools/run_benchmarks.py", "--tasks", tasks, "--split", split, "--report", str(split_dir / "benchmark.md"), "--json", str(benchmark_json)],
            repo_root,
        ),
        "ablation": _run(
            ["python", "tools/run_ablation.py", "--tasks", tasks, "--split", split, "--report", str(split_dir / "ablation.md"), "--json", str(ablation_json)],
            repo_root,
        ),
        "determinism": _run(
            ["python", "tools/check_determinism.py", "--tasks", tasks, "--split", split, "--runs", "5", "--report", str(split_dir / "determinism.md"), "--json", str(determinism_json)],
            repo_root,
        ),
        "failures": _run(
            ["python", "tools/summarize_failures.py", "--input", str(benchmark_json), "--output", str(split_dir / "failures.md"), "--json", str(failures_json)],
            repo_root,
        ),
        "scorecard": _run(
            [
                "python",
                "tools/generate_scorecard.py",
                "--benchmark",
                str(benchmark_json),
                "--ablation",
                str(ablation_json),
                "--determinism",
                str(determinism_json),
                "--failures",
                str(failures_json),
                "--output",
                str(scorecard_json),
                "--markdown",
                str(split_dir / "scorecard.md"),
            ],
            repo_root,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the full ARC solver validation battery.")
    parser.add_argument("--tasks", default="data/fixtures", help="Fixture task directory.")
    parser.add_argument("--reports", default="reports", help="Report output directory.")
    parser.add_argument(
        "--splits",
        nargs="*",
        default=["all"],
        help="Splits to evaluate. Use all, dev, regression, blind_holdout, or omit for all.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / args.reports
    reports_dir.mkdir(parents=True, exist_ok=True)
    available_splits = set(discover_splits(repo_root / "data/splits"))
    requested_splits = ["all"] if args.splits == ["all"] else args.splits
    for split in requested_splits:
        if split != "all" and split not in available_splits:
            raise ValueError(f"Unknown split: {split}")

    results: dict[str, object] = {
        "unit_and_integration": _run(["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], repo_root),
        "regressions": _run(["python", "-m", "unittest", "tests.test_regressions"], repo_root),
        "split_runs": {},
    }
    for split in requested_splits:
        results["split_runs"][split] = _bench_suite(repo_root, reports_dir, args.tasks, split)

    write_json(reports_dir / "test_results.json", json.dumps(results, indent=2, sort_keys=True))
    lines = []
    for name in ("unit_and_integration", "regressions"):
        payload = results[name]
        lines.append(f"[{name}] returncode={payload['returncode']}")
        if payload["stdout"]:
            lines.append(payload["stdout"].strip())
        if payload["stderr"]:
            lines.append(payload["stderr"].strip())
        lines.append("")
    for split, suite in results["split_runs"].items():
        lines.append(f"[split={split}]")
        for name, payload in suite.items():
            lines.append(f"  {name}: returncode={payload['returncode']}")
        lines.append("")
    write_json(reports_dir / "test_results.txt", "\n".join(lines))

    split_scorecards: dict[str, dict[str, object]] = {}
    for split in requested_splits:
        summary_dir = _split_output_dir(reports_dir, split)
        benchmark = json.loads((summary_dir / "benchmark.json").read_text(encoding="utf-8"))
        ablation = json.loads((summary_dir / "ablation.json").read_text(encoding="utf-8"))
        failures = json.loads((summary_dir / "failures.json").read_text(encoding="utf-8"))
        determinism = json.loads((summary_dir / "determinism.json").read_text(encoding="utf-8"))
        write_json(summary_dir / "per_task_diagnostics.json", json.dumps(benchmark.get("per_task", []), indent=2, sort_keys=True))
        write_json(
            summary_dir / "next_stage_summary.md",
            next_stage_summary_markdown(benchmark, ablation, failures, determinism),
        )
        # Collect scorecard for multi-split summary (A: split-specific reporting)
        scorecard_path = summary_dir / "scorecard.json"
        if scorecard_path.exists():
            split_scorecards[split] = json.loads(scorecard_path.read_text(encoding="utf-8"))

    # Generate the aggregate multi-split summary (A: no more collapsing to "all")
    if len(split_scorecards) > 1:
        write_json(
            reports_dir / "multi_split_summary.md",
            multi_split_summary_markdown(split_scorecards),
        )

    # Generate final split diagnostics table (A+B: machine-readable + blind holdout verdict)
    final_diag = _run(
        ["python", "tools/generate_final_split_diagnostics.py", "--reports", str(reports_dir)],
        repo_root,
    )
    if final_diag["returncode"] != 0:
        print(f"[WARN] generate_final_split_diagnostics failed: {final_diag['stderr']}")

    # Generate uncertainty audit (D: uncertainty usefulness check)
    uncertainty_audit = _run(
        ["python", "tools/generate_uncertainty_audit.py", "--reports", str(reports_dir)],
        repo_root,
    )
    if uncertainty_audit["returncode"] != 0:
        print(f"[WARN] generate_uncertainty_audit failed: {uncertainty_audit['stderr']}")

    # Generate epistemic reordering analysis (C: first-pass vs final ranking comparison)
    epistemic_reorderings = _run(
        ["python", "tools/generate_epistemic_reorderings.py", "--reports", str(reports_dir)],
        repo_root,
    )
    if epistemic_reorderings["returncode"] != 0:
        print(f"[WARN] generate_epistemic_reorderings failed: {epistemic_reorderings['stderr']}")

    # Generate thesis validation summary (F: answer the six core thesis questions)
    thesis_validation = _run(
        ["python", "tools/generate_thesis_validation_summary.py", "--reports", str(reports_dir)],
        repo_root,
    )
    if thesis_validation["returncode"] != 0:
        print(f"[WARN] generate_thesis_validation_summary failed: {thesis_validation['stderr']}")

    failed = any(results[name]["returncode"] != 0 for name in ("unit_and_integration", "regressions"))
    for suite in results["split_runs"].values():
        failed = failed or any(payload["returncode"] != 0 for payload in suite.values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
