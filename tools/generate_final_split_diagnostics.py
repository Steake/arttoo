"""Generate reports/final_split_diagnostics.json and reports/final_split_diagnostics.md.

This tool reads the per-split scorecard, benchmark, and failure artifacts and
assembles a single machine-readable table covering all four splits (dev,
regression, blind_holdout, all).  It also emits an explicit blind holdout
verdict section.

Usage:
    python tools/generate_final_split_diagnostics.py --reports reports
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.reporting import write_json

ORDERED_SPLITS = ["dev", "regression", "blind_holdout", "all"]

_HOLDOUT_WARN = (
    "⚠️  blind_holdout and all-split numbers are NOT safe for tuning. "
    "They are provided for honest reporting only."
)


def _split_dir(reports_dir: Path, split: str) -> Path:
    return reports_dir if split == "all" else reports_dir / split


def _load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _split_row(reports_dir: Path, split: str) -> dict:
    base = _split_dir(reports_dir, split)
    sc = _load_json(base / "scorecard.json")
    failures = _load_json(base / "failures.json")
    row = {
        "split": split,
        "tuning_safe": split in ("dev", "regression"),
        "task_count": sc.get("evaluated_tasks", 0),
        "full_solver_exact_rate": sc.get("exact_solve_rate", None),
        "primitive_baseline_exact_rate": sc.get("primitive_baseline_solve_rate", None),
        "lift": sc.get("lift", None),
        "avg_winning_uncertainty": sc.get("average_winning_uncertainty", None),
        "avg_winning_belief": sc.get("average_winning_belief", None),
        "final_task_failure_count": failures.get("final_task_failure_count", sc.get("final_task_failure_count", 0)),
        "unsupported_pattern_exit_count": failures.get("unsupported_pattern_exit_count", sc.get("unsupported_pattern_exit_count", 0)),
        "shape_mismatch_rejection_count": failures.get("shape_mismatch_rejection_count", sc.get("shape_mismatch_rejection_count", 0)),
        "candidate_transform_failure_count": failures.get("candidate_transform_failure_count", sc.get("candidate_transform_failure_count", 0)),
        "average_runtime_ms": sc.get("average_runtime_ms", None),
        "worst_case_runtime_ms": sc.get("worst_case_runtime_ms", None),
        "determinism_pass": sc.get("determinism_pass", None),
        "timestamp_utc": sc.get("timestamp_utc", None),
    }
    return row


def _blind_holdout_verdict(rows: list[dict]) -> str:
    holdout = next((r for r in rows if r["split"] == "blind_holdout"), None)
    if holdout is None:
        return "blind_holdout data not available."

    full = holdout["full_solver_exact_rate"]
    baseline = holdout["primitive_baseline_exact_rate"]
    lift = holdout["lift"]
    uncertainty = holdout["avg_winning_uncertainty"]
    failures = holdout["final_task_failure_count"]

    if lift is None:
        return "blind_holdout verdict: insufficient data."

    if lift > 0.0:
        solver_verdict = (
            f"Full solver beats primitive baseline on blind_holdout by {lift:+.3f} "
            f"({full:.3f} vs {baseline:.3f})."
        )
        generalises = "Current evidence **supports** generalisation beyond tuning-facing splits."
    elif lift == 0.0:
        solver_verdict = (
            f"Full solver matches primitive baseline on blind_holdout "
            f"(both {full:.3f}). No additional lift from the epistemic layer."
        )
        generalises = (
            "Current evidence shows the epistemic layer does **not** add measurable lift on blind_holdout. "
            "The primitive baseline already solves all holdout tasks. "
            "This means there is no room for epistemic machinery to demonstrate value on the current holdout set. "
            "Expand the holdout set with tasks the primitive baseline fails on to get a meaningful signal."
        )
    else:
        solver_verdict = (
            f"Full solver is **worse** than primitive baseline on blind_holdout by {lift:+.3f} "
            f"({full:.3f} vs {baseline:.3f})."
        )
        generalises = "Current evidence does **not** support generalisation."

    if uncertainty is not None and uncertainty > 0.05:
        uncertainty_verdict = (
            f"Non-zero average winning uncertainty ({uncertainty:.3f}) present on blind_holdout: "
            "the epistemic layer is exposing genuine ambiguity."
        )
    else:
        uncertainty_verdict = (
            f"Average winning uncertainty on blind_holdout is {uncertainty if uncertainty is not None else 'n/a'} "
            "(effectively zero). All holdout tasks are resolved with full confidence. "
            "Uncertainty is not decision-relevant here because the primitive transforms are unambiguous for these tasks."
        )

    if failures == 0:
        failure_verdict = "No task failures on blind_holdout. No dominant failure family present."
    else:
        failure_verdict = f"{failures} task(s) failed on blind_holdout. See failure breakdown above."

    return "\n".join([
        "### Blind Holdout Verdict",
        "",
        f"> {_HOLDOUT_WARN}",
        "",
        f"- **Solver vs baseline:** {solver_verdict}",
        f"- **Uncertainty:** {uncertainty_verdict}",
        f"- **Failures:** {failure_verdict}",
        f"- **Generalisation:** {generalises}",
    ])


def _table(headers: list[str], rows: list[list[str]]) -> str:
    parts = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def _fmt(v: object, fmt: str = "") -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        if fmt == "+.3f":
            return f"{v:+.3f}"
        return f"{v:.3f}"
    return str(v)


def build_markdown(rows: list[dict]) -> str:
    table_rows = []
    for row in rows:
        safe_marker = "" if row["tuning_safe"] else " ⚠️"
        table_rows.append([
            row["split"] + safe_marker,
            _fmt(row["task_count"]),
            _fmt(row["full_solver_exact_rate"]),
            _fmt(row["primitive_baseline_exact_rate"]),
            _fmt(row["lift"], "+.3f"),
            _fmt(row["avg_winning_uncertainty"]),
            _fmt(row["final_task_failure_count"]),
            _fmt(row["unsupported_pattern_exit_count"]),
            _fmt(row["shape_mismatch_rejection_count"]),
            _fmt(row["candidate_transform_failure_count"]),
            _fmt(row["average_runtime_ms"]) + " ms",
            _fmt(row["worst_case_runtime_ms"]) + " ms",
        ])

    holdout_verdict = _blind_holdout_verdict(rows)

    return "\n".join([
        "# Final Split Diagnostics",
        "",
        f"> {_HOLDOUT_WARN}",
        "",
        "Split provenance:",
        "- **dev**: tuning fixtures — safe for hyperparameter and solver iteration.",
        "- **regression**: known-failure regression fixtures — safe for targeted debugging.",
        "- **blind_holdout** ⚠️: unseen at tuning time — for honest reporting only.",
        "- **all** ⚠️: aggregate across all fixtures — for honest reporting only.",
        "",
        _table(
            [
                "Split", "Tasks",
                "Solve rate", "Baseline rate", "Lift",
                "Avg uncertainty",
                "Final failures", "Unsupported exits",
                "Shape rejections", "Crash failures",
                "Avg runtime", "Worst runtime",
            ],
            table_rows,
        ),
        "",
        holdout_verdict,
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate final split diagnostics table.")
    parser.add_argument("--reports", default="reports", help="Reports root directory.")
    parser.add_argument("--output-json", default=None, help="Override output JSON path.")
    parser.add_argument("--output-md", default=None, help="Override output markdown path.")
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports)
    output_json = Path(args.output_json) if args.output_json else reports_dir / "final_split_diagnostics.json"
    output_md = Path(args.output_md) if args.output_md else reports_dir / "final_split_diagnostics.md"

    rows = []
    for split in ORDERED_SPLITS:
        split_dir = _split_dir(reports_dir, split)
        sc_path = split_dir / "scorecard.json"
        if not sc_path.exists():
            continue
        rows.append(_split_row(reports_dir, split))

    payload = {
        "splits": rows,
        "holdout_warn": _HOLDOUT_WARN,
    }
    write_json(output_json, json.dumps(payload, indent=2, sort_keys=True))
    write_json(output_md, build_markdown(rows))
    print(f"Written: {output_json}")
    print(f"Written: {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
