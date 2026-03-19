from __future__ import annotations

"""Generate the thesis validation summary.

Answers the six core questions about the epistemic co-agency thesis directly
and without ambiguity:

  1. Is blind_holdout currently discriminative?
  2. Does the full solver beat the primitive baseline on blind_holdout?
  3. Is uncertainty present on any solved tasks?
  4. Is uncertainty decision-relevant?
  5. Do epistemic reorderings occur?
  6. Is current evidence sufficient to claim generalisation of epistemic
     co-agency beyond tuning-facing splits?

Reads:
  - reports/final_split_diagnostics.json
  - reports/epistemic_reorderings.json
  - reports/blind_holdout/per_task_diagnostics.json  (if available)
  - reports/regression/per_task_diagnostics.json     (if available)

Emits:
  - reports/thesis_validation_summary.json
  - reports/thesis_validation_summary.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.reporting import write_json

_DISCRIMINATIVE_THRESHOLD = 1  # Min holdout tasks primitive baseline must fail.


def _load_json(path: Path) -> dict | list | None:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _holdout_discriminative(split_diagnostics: dict) -> tuple[bool, str]:
    """Return (is_discriminative, explanation)."""
    holdout = split_diagnostics.get("blind_holdout", {})
    if not holdout:
        return (False, "blind_holdout data not available in final_split_diagnostics.json.")
    baseline_rate = holdout.get(
        "primitive_baseline_exact_rate", holdout.get("baseline_rate", 1.0)
    )
    full_rate = holdout.get(
        "full_solver_exact_rate", holdout.get("full_solve_rate", 0.0)
    )
    task_count = holdout.get("task_count", 0)

    if baseline_rate < 1.0:
        failed_tasks = round((1.0 - baseline_rate) * task_count)
        return (
            True,
            f"Primitive baseline fails {failed_tasks}/{task_count} blind_holdout tasks"
            f" (rate={baseline_rate:.3f}).  The holdout is discriminative: it contains tasks"
            " that require epistemic refinement (composition) to solve.",
        )
    if full_rate > baseline_rate:
        return (
            True,
            f"Full solver ({full_rate:.3f}) beats primitive baseline ({baseline_rate:.3f})"
            " on blind_holdout, even though baseline already achieves some correctness."
            " The holdout is marginally discriminative.",
        )
    return (
        False,
        f"Primitive baseline already achieves {baseline_rate:.3f} on all blind_holdout tasks"
        " and the full solver provides no additional lift.  The current holdout is NOT"
        " discriminative enough to test the thesis.  Expand it with harder tasks.",
    )


def _full_beats_baseline(split_diagnostics: dict) -> tuple[bool, str]:
    holdout = split_diagnostics.get("blind_holdout", {})
    if not holdout:
        return (False, "blind_holdout data not available.")
    baseline_rate = holdout.get(
        "primitive_baseline_exact_rate", holdout.get("baseline_rate", 1.0)
    )
    full_rate = holdout.get(
        "full_solver_exact_rate", holdout.get("full_solve_rate", 0.0)
    )
    task_count = holdout.get("task_count", 0)
    lift = full_rate - baseline_rate
    if lift > 0:
        return (
            True,
            f"Full solver={full_rate:.3f}, primitive baseline={baseline_rate:.3f},"
            f" lift=+{lift:.3f} on {task_count} blind_holdout tasks.",
        )
    elif lift == 0:
        return (
            False,
            f"Full solver ({full_rate:.3f}) matches primitive baseline ({baseline_rate:.3f}) on"
            f" blind_holdout ({task_count} tasks).  No measured lift.",
        )
    else:
        return (
            False,
            f"Full solver ({full_rate:.3f}) is BELOW primitive baseline ({baseline_rate:.3f}) on"
            f" blind_holdout.  Regression on holdout — investigate before further tuning.",
        )


def _uncertainty_present_on_solved(
    per_task_diagnostics: list[dict],
    splits_to_check: list[str],
) -> tuple[bool, str]:
    """Check if any solved task has non-zero first-pass winning uncertainty."""
    found: list[str] = []
    for record in per_task_diagnostics:
        split = record.get("split", "")
        if split not in splits_to_check:
            continue
        if record.get("variant") not in ("full_epistemic_coagency", None):
            continue
        solved = record.get("success_attempt_1", False)
        if not solved:
            continue
        telemetry = record.get("telemetry", {})
        first_pass = telemetry.get("first_pass_ranking", [])
        if first_pass and float(first_pass[0].get("uncertainty", 0.0)) > 0.0:
            found.append(f"{record['task_id']} (split={split})")
    if found:
        return (
            True,
            f"Non-zero first-pass uncertainty on {len(found)} solved task(s): "
            + ", ".join(found[:5])
            + ("..." if len(found) > 5 else ".")
            + "  This means the first-pass winner did not fully explain all training pairs"
            " before refinement corrected it.",
        )
    return (
        False,
        "All solved tasks have zero first-pass winning uncertainty.  Every solved task is"
        " explained with complete certainty by a single primitive (or composition) from the"
        " first pass.  Add composition tasks to create non-zero first-pass uncertainty on"
        " solved tasks.",
    )


def _uncertainty_decision_relevant(reorderings: dict) -> tuple[bool, str]:
    """Uncertainty is decision-relevant if reorderings occur on solved tasks."""
    total_success = sum(
        v.get("reorder_success_count", 0)
        for k, v in reorderings.items()
    )
    total_reorderings = sum(
        v.get("tasks_where_first_pass_winner_changed_after_refinement", 0)
        for k, v in reorderings.items()
    )
    if total_success > 0:
        return (
            True,
            f"{total_success} successful reordering(s) across all splits: refinement replaced"
            " a non-certain first-pass winner with a correct composed hypothesis.  Uncertainty"
            " (non-zero on the first-pass winner) directly determined the final answer.",
        )
    if total_reorderings > 0:
        return (
            False,
            f"{total_reorderings} reordering(s) detected but none led to a correct final answer."
            "  Uncertainty influenced ranking but did not improve outcomes in the current suite.",
        )
    return (
        False,
        "No reorderings detected.  Uncertainty has not yet affected final hypothesis selection"
        " in any evaluated task.  The ranking is effectively driven by belief alone.",
    )


def _reorderings_occur(reorderings: dict) -> tuple[bool, str]:
    total = sum(
        v.get("tasks_where_first_pass_winner_changed_after_refinement", 0)
        for k, v in reorderings.items()
    )
    by_split = {
        k: v.get("tasks_where_first_pass_winner_changed_after_refinement", 0)
        for k, v in reorderings.items()
    }
    if total > 0:
        detail = ", ".join(f"{s}={n}" for s, n in sorted(by_split.items()) if n > 0)
        return (True, f"{total} reordering(s) detected ({detail}).")
    return (False, "Zero reorderings across all splits and variants.")


def _generalisation_claim(
    discriminative: bool,
    full_beats: bool,
    reorderings_occur: bool,
) -> tuple[str, str, str]:
    """Return (proven, suggested, untestable) strings."""
    proven_parts: list[str] = []
    suggested_parts: list[str] = []
    untestable_parts: list[str] = []

    if full_beats:
        proven_parts.append(
            "Full solver beats primitive baseline on blind_holdout (measured lift > 0)."
        )
    if reorderings_occur:
        proven_parts.append(
            "Epistemic refinement reorders candidates in at least one task, demonstrating"
            " that the co-agency loop provides value beyond the first-pass primitives."
        )
    if not discriminative:
        untestable_parts.append(
            "blind_holdout is not sufficiently discriminative to test generalisation:"
            " primitive baseline saturates it.  Generalisation cannot be confirmed or"
            " denied from the current holdout."
        )
    if discriminative and not full_beats:
        suggested_parts.append(
            "blind_holdout is discriminative (baseline fails some tasks) but the full solver"
            " does not yet improve over baseline on holdout.  Generalisation is suggested"
            " by the design but not proven by current numbers."
        )
    if discriminative and full_beats and not reorderings_occur:
        suggested_parts.append(
            "Full solver beats primitive baseline on holdout, but no epistemic reorderings"
            " have been measured.  The lift may come from the refinement pass alone rather"
            " than from uncertainty-aware ranking."
        )

    proven = (
        "  ".join(proven_parts)
        if proven_parts
        else "Nothing has been formally proven yet about generalisation."
    )
    suggested = (
        "  ".join(suggested_parts)
        if suggested_parts
        else "No additional evidence suggests generalisation beyond what is proven."
    )
    untestable = (
        "  ".join(untestable_parts)
        if untestable_parts
        else "No known gaps in the current benchmark design."
    )
    return proven, suggested, untestable


def _markdown(answers: dict) -> str:
    def yn(val: bool) -> str:
        return "**YES**" if val else "**NO**"

    lines: list[str] = [
        "# Thesis Validation Summary",
        "",
        "> ⚠️  The `blind_holdout` column is for honest reporting only — not for tuning.",
        "",
        "This document answers the six core questions about the epistemic co-agency thesis.",
        "",
        "## Six Core Questions",
        "",
        f"### 1. Is blind_holdout currently discriminative?",
        "",
        f"{yn(answers['q1_discriminative'])}",
        "",
        answers["q1_explanation"],
        "",
        f"### 2. Does the full solver beat the primitive baseline on blind_holdout?",
        "",
        f"{yn(answers['q2_full_beats_baseline'])}",
        "",
        answers["q2_explanation"],
        "",
        f"### 3. Is uncertainty present on any solved tasks?",
        "",
        f"{yn(answers['q3_uncertainty_present'])}",
        "",
        answers["q3_explanation"],
        "",
        f"### 4. Is uncertainty decision-relevant?",
        "",
        f"{yn(answers['q4_uncertainty_decision_relevant'])}",
        "",
        answers["q4_explanation"],
        "",
        f"### 5. Do epistemic reorderings occur?",
        "",
        f"{yn(answers['q5_reorderings_occur'])}",
        "",
        answers["q5_explanation"],
        "",
        f"### 6. Is current evidence sufficient to claim generalisation?",
        "",
        "#### What is proven",
        "",
        answers["q6_proven"],
        "",
        "#### What is suggested but not proven",
        "",
        answers["q6_suggested"],
        "",
        "#### What remains untestable because of benchmark design",
        "",
        answers["q6_untestable"],
        "",
        "## Overall Verdict",
        "",
        answers["overall_verdict"],
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate thesis validation summary.")
    parser.add_argument("--reports", default="reports", help="Path to the reports directory.")
    args = parser.parse_args(argv)

    reports_dir = Path(args.reports).resolve()

    # Load required input artefacts.
    split_diagnostics_raw = _load_json(reports_dir / "final_split_diagnostics.json")
    reorderings_raw = _load_json(reports_dir / "epistemic_reorderings.json")

    if split_diagnostics_raw is None:
        print("[WARN] final_split_diagnostics.json not found. Run generate_final_split_diagnostics first.")
        split_diagnostics_raw = {}
    if reorderings_raw is None:
        print("[WARN] epistemic_reorderings.json not found. Run generate_epistemic_reorderings first.")
        reorderings_raw = {}

    # Collect per-task diagnostics for uncertainty analysis.
    per_task_all: list[dict] = []
    for candidate in sorted(reports_dir.iterdir()):
        if candidate.is_dir():
            diag_path = candidate / "per_task_diagnostics.json"
            if diag_path.exists():
                per_task_all.extend(json.loads(diag_path.read_text(encoding="utf-8")))
    root_diag = reports_dir / "per_task_diagnostics.json"
    if root_diag.exists():
        per_task_all.extend(json.loads(root_diag.read_text(encoding="utf-8")))

    # Normalise split_diagnostics: it may be a list-of-rows, a dict with a
    # "splits" key (as emitted by generate_final_split_diagnostics.py), or a
    # flat dict keyed by split name.
    split_diagnostics: dict[str, dict] = {}
    if isinstance(split_diagnostics_raw, dict):
        if "splits" in split_diagnostics_raw:
            # Format emitted by generate_final_split_diagnostics.py:
            # {"splits": [{"split": "dev", ...}, ...], ...}
            for row in split_diagnostics_raw["splits"]:
                s = row.get("split", "")
                if s:
                    split_diagnostics[s] = row
        else:
            split_diagnostics = split_diagnostics_raw  # type: ignore[assignment]
    elif isinstance(split_diagnostics_raw, list):
        for row in split_diagnostics_raw:
            s = row.get("split", "")
            if s:
                split_diagnostics[s] = row

    # Answer the six questions.
    q1, q1_exp = _holdout_discriminative(split_diagnostics)
    q2, q2_exp = _full_beats_baseline(split_diagnostics)
    q3, q3_exp = _uncertainty_present_on_solved(per_task_all, ["regression", "blind_holdout"])
    q4, q4_exp = _uncertainty_decision_relevant(reorderings_raw)
    q5, q5_exp = _reorderings_occur(reorderings_raw)
    q6_proven, q6_suggested, q6_untestable = _generalisation_claim(q1, q2, q5)

    # Overall verdict.
    if q1 and q2 and q5:
        overall_verdict = (
            "The thesis is currently **testable and shows positive evidence**: the holdout is"
            " discriminative, the full solver outperforms the primitive baseline on unseen tasks,"
            " and epistemic reorderings have been observed.  Further evidence is needed to"
            " establish that uncertainty-aware ranking (rather than refinement alone) drives the lift."
        )
    elif q1 and q2:
        overall_verdict = (
            "The holdout is discriminative and the full solver beats the baseline on unseen tasks."
            " However, no epistemic reorderings have been measured, so the lift may come from"
            " the refinement composition pass rather than from uncertainty-aware ranking specifically."
        )
    elif q1:
        overall_verdict = (
            "The holdout is discriminative (baseline fails some tasks), but the full solver has"
            " not yet demonstrated a measurable lift.  The thesis is testable but not yet confirmed."
        )
    else:
        overall_verdict = (
            "The holdout is NOT discriminative: the primitive baseline already solves all holdout"
            " tasks.  The thesis cannot be tested on the current holdout.  Expand the holdout with"
            " tasks that require composition or epistemic disambiguation."
        )

    answers: dict[str, object] = {
        "q1_discriminative": q1,
        "q1_explanation": q1_exp,
        "q2_full_beats_baseline": q2,
        "q2_explanation": q2_exp,
        "q3_uncertainty_present": q3,
        "q3_explanation": q3_exp,
        "q4_uncertainty_decision_relevant": q4,
        "q4_explanation": q4_exp,
        "q5_reorderings_occur": q5,
        "q5_explanation": q5_exp,
        "q6_proven": q6_proven,
        "q6_suggested": q6_suggested,
        "q6_untestable": q6_untestable,
        "overall_verdict": overall_verdict,
    }

    write_json(
        reports_dir / "thesis_validation_summary.json",
        json.dumps(answers, indent=2, sort_keys=True),
    )
    write_json(reports_dir / "thesis_validation_summary.md", _markdown(answers))

    # Brief stdout.
    print(f"  discriminative_holdout={q1}")
    print(f"  full_beats_baseline={q2}")
    print(f"  uncertainty_present={q3}")
    print(f"  uncertainty_decision_relevant={q4}")
    print(f"  reorderings={q5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
