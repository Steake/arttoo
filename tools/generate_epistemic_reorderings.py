from __future__ import annotations

"""Generate epistemic reordering analysis across evaluation splits.

A "reordering" occurs when the first-pass winner (highest-ranked hypothesis
after the initial primitive evaluation) differs from the final winner after the
refinement pass.  This is the primary signal that the co-agency refinement loop
is providing value beyond first-pass heuristics.

Reads per_task_diagnostics.json for each split and produces:
  - reports/epistemic_reorderings.json
  - reports/epistemic_reorderings.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.reporting import write_json


def _competing_candidates_count(first_pass_ranking: list[dict]) -> int:
    """Count hypotheses in the first pass that are viable (not purely contradicted).

    A hypothesis is considered viable if it has any belief > 0, unresolved
    support (uncertainty > 0), or a score strictly above -1.0.  This captures
    candidates that survived early filtering with at least partial evidence.
    """
    return sum(
        1
        for h in first_pass_ranking
        if h.get("belief", 0.0) > 0.0
        or h.get("uncertainty", 0.0) > 0.0
        or h.get("score", -1.0) > -1.0
    )


def _analyse_split(per_task_diagnostics: list[dict], split: str) -> dict:
    """Compute reordering statistics for a single split."""
    # Only use the full co-agency variant for the thesis analysis.
    full_coagency_tasks = [
        t for t in per_task_diagnostics
        if t.get("variant") == "full_epistemic_coagency" and t.get("split") == split
    ]
    if not full_coagency_tasks:
        # Fall back to all records for the split when variant info is absent.
        full_coagency_tasks = [t for t in per_task_diagnostics if t.get("split") == split]

    task_count = len(full_coagency_tasks)
    tasks_with_multiple_competing_candidates = 0
    tasks_with_nonzero_winning_uncertainty = 0
    tasks_where_first_pass_winner_changed = 0
    reorder_success_count = 0
    reorder_failure_count = 0
    unchanged_correct_count = 0
    unchanged_incorrect_count = 0
    per_task_details: list[dict] = []

    for task in full_coagency_tasks:
        task_id = task.get("task_id", "unknown")
        solved = bool(task.get("success_attempt_1", False))
        telemetry = task.get("telemetry", {})
        first_pass_ranking = telemetry.get("first_pass_ranking", [])
        final_ranking = telemetry.get("final_ranking", [])

        # First-pass winner description.
        first_winner = first_pass_ranking[0]["description"] if first_pass_ranking else None
        final_winner = final_ranking[0]["description"] if final_ranking else None

        # Competing candidates: at least 2 viable hypotheses in first pass.
        competing = _competing_candidates_count(first_pass_ranking)
        if competing >= 2:
            tasks_with_multiple_competing_candidates += 1

        # Winning first-pass uncertainty.
        first_winner_uncertainty = (
            float(first_pass_ranking[0].get("uncertainty", 0.0)) if first_pass_ranking else 0.0
        )
        if first_winner_uncertainty > 0.0:
            tasks_with_nonzero_winning_uncertainty += 1

        # Reordering detection.
        reordered = (
            first_winner is not None
            and final_winner is not None
            and first_winner != final_winner
        )
        if reordered:
            tasks_where_first_pass_winner_changed += 1
            if solved:
                reorder_success_count += 1
            else:
                reorder_failure_count += 1
        else:
            if solved:
                unchanged_correct_count += 1
            else:
                unchanged_incorrect_count += 1

        # Top-candidate details for the per-task record.
        top_candidates = [
            {
                "description": h.get("description", ""),
                "family": h.get("family", ""),
                "belief": h.get("belief", 0.0),
                "disbelief": h.get("disbelief", 0.0),
                "uncertainty": h.get("uncertainty", 0.0),
                "score": h.get("score", -1.0),
            }
            for h in first_pass_ranking[:5]
        ]
        pruned_reasons = [
            p.get("reason", "") for p in telemetry.get("first_pass_pruned", [])
        ]

        per_task_details.append(
            {
                "task_id": task_id,
                "split": split,
                "solved": solved,
                "first_pass_winner": first_winner,
                "final_winner": final_winner,
                "reordered": reordered,
                "reorder_correct": reordered and solved,
                "competing_candidates_count": competing,
                "first_pass_winner_uncertainty": first_winner_uncertainty,
                "top_first_pass_candidates": top_candidates,
                "first_pass_pruned_reasons": pruned_reasons,
            }
        )

    return {
        "split": split,
        "task_count": task_count,
        "tasks_with_multiple_competing_candidates": tasks_with_multiple_competing_candidates,
        "tasks_with_nonzero_winning_uncertainty": tasks_with_nonzero_winning_uncertainty,
        "tasks_where_first_pass_winner_changed_after_refinement": tasks_where_first_pass_winner_changed,
        "reorder_success_count": reorder_success_count,
        "reorder_failure_count": reorder_failure_count,
        "unchanged_correct_count": unchanged_correct_count,
        "unchanged_incorrect_count": unchanged_incorrect_count,
        "per_task": per_task_details,
    }


def _table(headers: list[str], rows: list[list[str]]) -> str:
    parts = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def _markdown(results: dict[str, dict], reports_dir: Path) -> str:
    lines: list[str] = [
        "# Epistemic Reordering Analysis",
        "",
        "> A **reordering** occurs when the first-pass winner (highest-ranked primitive hypothesis) is"
        " replaced by a different hypothesis after the refinement pass.  Reorderings are the primary"
        " operational signal that the co-agency refinement loop adds value beyond the primitive"
        " baseline.",
        "",
        "## Summary by Split",
        "",
    ]
    headers = [
        "Split", "Tasks", "Multiple competing candidates",
        "Nonzero 1st-pass uncertainty", "Reorderings",
        "Reorder success", "Reorder failure",
        "Unchanged correct", "Unchanged incorrect",
    ]
    rows = []
    for split, stats in sorted(results.items()):
        if split == "per_task":
            continue
        rows.append([
            split,
            str(stats["task_count"]),
            str(stats["tasks_with_multiple_competing_candidates"]),
            str(stats["tasks_with_nonzero_winning_uncertainty"]),
            str(stats["tasks_where_first_pass_winner_changed_after_refinement"]),
            str(stats["reorder_success_count"]),
            str(stats["reorder_failure_count"]),
            str(stats["unchanged_correct_count"]),
            str(stats["unchanged_incorrect_count"]),
        ])
    lines.append(_table(headers, rows))
    lines.append("")
    lines.append("## Column Definitions")
    lines.append("")
    lines.append("- **Multiple competing candidates**: tasks where ≥ 2 first-pass hypotheses are viable")
    lines.append("  (non-zero belief, uncertainty, or score > −1.0).")
    lines.append("- **Nonzero 1st-pass uncertainty**: tasks where the first-pass winner has uncertainty > 0,")
    lines.append("  meaning it did not perfectly explain all training pairs.")
    lines.append("- **Reorderings**: tasks where `first_pass_winner ≠ final_winner` after refinement.")
    lines.append("- **Reorder success**: reordering occurred AND task was ultimately solved correctly.")
    lines.append("- **Reorder failure**: reordering occurred AND task was still solved incorrectly.")
    lines.append("- **Unchanged correct**: no reordering AND task solved correctly.")
    lines.append("- **Unchanged incorrect**: no reordering AND task still wrong.")
    lines.append("")

    # Per-split per-task detail tables.
    for split, stats in sorted(results.items()):
        if split == "per_task":
            continue
        if not stats.get("per_task"):
            continue
        lines.append(f"## Per-Task Detail: {split}")
        lines.append("")
        pt_headers = [
            "Task", "Solved", "1st-pass winner", "Final winner",
            "Reordered", "Competing", "1st-pass uncertainty",
        ]
        pt_rows = [
            [
                t["task_id"],
                "yes" if t["solved"] else "no",
                t["first_pass_winner"] or "none",
                t["final_winner"] or "none",
                "yes" if t["reordered"] else "no",
                str(t["competing_candidates_count"]),
                f'{t["first_pass_winner_uncertainty"]:.3f}',
            ]
            for t in stats["per_task"]
        ]
        lines.append(_table(pt_headers, pt_rows))
        lines.append("")

    # Interpretation verdict.
    lines.append("## Verdict")
    lines.append("")
    all_reorderings = sum(
        v["tasks_where_first_pass_winner_changed_after_refinement"]
        for k, v in results.items()
        if k != "per_task"
    )
    all_successes = sum(
        v["reorder_success_count"] for k, v in results.items() if k != "per_task"
    )
    if all_reorderings == 0:
        lines.append(
            "**No reorderings detected across any split.**  The refinement pass did not change the"
            " top-ranked hypothesis in any task.  This indicates either (a) all tasks are solved"
            " by a single primitive in the first pass, or (b) the composed hypothesis happened to"
            " agree with the first-pass winner.  Add composition tasks (where no single primitive"
            " perfectly explains all training pairs) to observe reorderings."
        )
    else:
        lines.append(
            f"**{all_reorderings} reordering(s) detected, {all_successes} successful** (refinement"
            " found the correct answer after changing the first-pass winner)."
        )
        lines.append(
            "Reorderings confirm that the co-agency refinement loop is providing value: the first-pass"
            " hypothesis was replaced by a composition that better explains the training evidence."
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate epistemic reordering analysis.")
    parser.add_argument("--reports", default="reports", help="Path to the reports directory.")
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports).resolve()
    # Collect per-task diagnostics from all available splits.
    all_diagnostics: list[dict] = []
    split_names: list[str] = []
    for candidate in sorted(reports_dir.iterdir()):
        if candidate.is_dir():
            diag_path = candidate / "per_task_diagnostics.json"
            if diag_path.exists():
                records = json.loads(diag_path.read_text(encoding="utf-8"))
                all_diagnostics.extend(records)
                split_names.append(candidate.name)
    # Also check root-level per_task_diagnostics (the "all" aggregate).
    root_diag = reports_dir / "per_task_diagnostics.json"
    if root_diag.exists():
        all_diagnostics.extend(json.loads(root_diag.read_text(encoding="utf-8")))
        split_names.append("all")

    if not all_diagnostics:
        print("[WARN] No per_task_diagnostics.json found under reports. Run the benchmark first.")
        return 1

    # De-duplicate: keep each (task_id, split, variant) once.
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict] = []
    for record in all_diagnostics:
        key = (
            record.get("task_id", ""),
            record.get("split", ""),
            record.get("variant", ""),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(record)

    results: dict[str, dict] = {}
    for split in split_names:
        stats = _analyse_split(deduped, split)
        if stats["task_count"] > 0:
            results[split] = stats

    # Write JSON (exclude per_task from top-level to keep summary compact).
    summary: dict[str, object] = {}
    for split, stats in results.items():
        summary[split] = {k: v for k, v in stats.items() if k != "per_task"}
    write_json(reports_dir / "epistemic_reorderings.json", json.dumps(summary, indent=2, sort_keys=True))
    write_json(reports_dir / "epistemic_reorderings.md", _markdown(results, reports_dir))

    # Print brief stdout summary.
    for split, stats in sorted(results.items()):
        print(
            f"  [{split}] reorderings={stats['tasks_where_first_pass_winner_changed_after_refinement']}"
            f"  success={stats['reorder_success_count']}"
            f"  competing={stats['tasks_with_multiple_competing_candidates']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
