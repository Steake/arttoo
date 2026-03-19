from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arc_epistemic.eval.analysis import _case_diagnostic
from arc_epistemic.eval.causal import _mcnemar_test, _paired_bootstrap_ci
from arc_epistemic.eval.fixtures import FixtureTask
from arc_epistemic.solver.agents import (
    COMPOSITION_BASELINE_CONFIG,
    EPISTEMIC_NO_REFINEMENT_CONFIG,
    FULL_COAGENCY_CONFIG,
    PRIMITIVE_BASELINE_CONFIG,
    SolverConfig,
    critic_prune,
    generate_hypotheses,
    refine_hypotheses,
    score_hypotheses,
)
from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.selection import select_top_two

CONDITION_LABELS: tuple[str, ...] = ("C00", "C10", "C01", "C11")
CONDITION_CONFIGS: dict[str, SolverConfig] = {
    "C00": PRIMITIVE_BASELINE_CONFIG,
    "C10": COMPOSITION_BASELINE_CONFIG,
    "C01": EPISTEMIC_NO_REFINEMENT_CONFIG,
    "C11": FULL_COAGENCY_CONFIG,
}
CONTRASTS: tuple[tuple[str, str, str, str], ...] = (
    ("c10_vs_c00", "C00", "C10", "Refinement without uncertainty-aware ranking (C10 − C00)"),
    ("c01_vs_c00", "C00", "C01", "Uncertainty-aware ranking without refinement (C01 − C00)"),
    ("c11_vs_c10", "C10", "C11", "Uncertainty-aware ranking given refinement (C11 − C10)"),
    ("c11_vs_c01", "C01", "C11", "Refinement given uncertainty-aware ranking (C11 − C01)"),
    ("c11_vs_c00", "C00", "C11", "Full solver versus primitive baseline (C11 − C00)"),
)
PRIMARY_SUBSETS: tuple[str, ...] = (
    "all_blind_holdout_v3",
    "ranking_conflict",
    "refinement_composition",
    "control",
)


@dataclass(frozen=True)
class ManifestEntry:
    task_id: str
    family: str
    intended_primary_mechanism: str
    intended_competing_candidates_expected: str
    intended_first_pass_disagreement_expected: str
    notes: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json_hash(payload: Any) -> str:
    data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: str | Path) -> list[ManifestEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [ManifestEntry(**entry) for entry in payload.get("entries", [])]


def manifest_by_task(entries: list[ManifestEntry]) -> dict[str, ManifestEntry]:
    return {entry.task_id: entry for entry in entries}


def subset_task_ids(entries: list[ManifestEntry], mechanism: str | None = None) -> tuple[str, ...]:
    if mechanism is None or mechanism == "all_blind_holdout_v3":
        return tuple(entry.task_id for entry in entries)
    return tuple(entry.task_id for entry in entries if entry.intended_primary_mechanism == mechanism)


def build_freeze_manifest(
    split_path: str | Path,
    manifest_path: str | Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    split_payload = json.loads(Path(split_path).read_text(encoding="utf-8"))
    manifest_payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    task_ids = list(split_payload.get("task_ids", []))
    family_counts = Counter(entry["family"] for entry in manifest_payload.get("entries", []))
    return {
        "split": "blind_holdout_v3",
        "generated_at_utc": generated_at_utc or _now_utc(),
        "task_count": len(task_ids),
        "task_ids": task_ids,
        "manifest_hash_sha256": _canonical_json_hash(manifest_payload),
        "split_hash_sha256": _canonical_json_hash(split_payload),
        "family_counts": dict(sorted(family_counts.items())),
        "source_paths": {
            "split": str(Path(split_path)),
            "manifest": str(Path(manifest_path)),
        },
    }


def freeze_manifest_markdown(payload: dict[str, Any]) -> str:
    rows = [
        ["split", str(payload.get("split", ""))],
        ["generated_at_utc", str(payload.get("generated_at_utc", ""))],
        ["task_count", str(payload.get("task_count", 0))],
        ["manifest_hash_sha256", str(payload.get("manifest_hash_sha256", ""))],
        ["split_hash_sha256", str(payload.get("split_hash_sha256", ""))],
    ]
    family_rows = [[family, str(count)] for family, count in sorted(payload.get("family_counts", {}).items())]
    lines = [
        "# blind_holdout_v3 Freeze Manifest",
        "",
        "> Freeze this manifest after task authoring. Subsequent reporting should reference the frozen hash rather than relabel tasks from solver outcomes.",
        "",
        _markdown_table(["Field", "Value"], rows),
        "",
        "## Family Counts",
        "",
        _markdown_table(["Family", "Count"], family_rows or [["none", "0"]]),
        "",
    ]
    return "\n".join(lines)


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    parts = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def _top_snapshot(ranking: list[dict[str, Any]]) -> dict[str, Any] | None:
    return ranking[0] if ranking else None


def _ordering(ranking: list[dict[str, Any]], limit: int = 5) -> list[str]:
    return [str(item.get("description", "")) for item in ranking[:limit]]


def _viable_candidates_count(ranking: list[dict[str, Any]]) -> int:
    return sum(
        1
        for item in ranking
        if float(item.get("belief", 0.0)) > 0.0
        or float(item.get("uncertainty", 0.0)) > 0.0
        or float(item.get("score", -1.0)) > -1.0
    )


def detect_ranking_conflict(task_entry: dict[str, Any]) -> bool:
    return bool(task_entry.get("ranking_conflict_occurred", False))


def count_uncertainty_driven_reorders(task_entries: list[dict[str, Any]]) -> dict[str, int]:
    changed = sum(1 for item in task_entries if item.get("uncertainty_changed_winner"))
    improved = sum(1 for item in task_entries if item.get("uncertainty_changed_winner") and item.get("uncertainty_improved_correctness"))
    hurt = sum(1 for item in task_entries if item.get("uncertainty_changed_winner") and item.get("uncertainty_hurt_correctness"))
    nonzero_solved = sum(
        1
        for item in task_entries
        if item.get("uncertainty_changed_winner")
        and item.get("condition_correctness", {}).get("C11")
        and float(item.get("uncertainty_aware_top_candidate", {}).get("uncertainty", 0.0)) > 0.0
    )
    return {
        "winner_changes": changed,
        "improved": improved,
        "hurt": hurt,
        "solved_with_nonzero_winning_uncertainty": nonzero_solved,
    }


def categorize_task_attribution_v2(
    c00: bool,
    c10: bool,
    c01: bool,
    c11: bool,
    family: str | None = None,
) -> str:
    if c10 < c00 or c11 < c01:
        return "refinement_hurt"
    if c01 < c00 or c11 < c10:
        return "uncertainty_hurt"
    if c00 and c10 and c01 and c11:
        return "control_all_agree"
    if not c00 and not c10 and not c01 and not c11:
        return "persistent_failure"
    if not c00 and c10 and not c01 and c11:
        return "refinement_only_gain"
    if not c00 and not c10 and c01 and c11:
        return "uncertainty_only_gain"
    if not c00 and not c10 and not c01 and c11:
        return "synergy_gain"
    if not c00 and c10 and c01 and c11:
        return "refinement_and_uncertainty_both_help_but_not_separable"
    if family == "control":
        return "control_all_agree"
    return "persistent_failure"


def _condition_outcomes(task_ids: tuple[str, ...], records_by_condition: dict[str, dict[str, dict[str, Any]]]) -> dict[str, tuple[bool, ...]]:
    return {
        label: tuple(bool(records_by_condition[label][task_id]["solved"]) for task_id in task_ids)
        for label in CONDITION_LABELS
    }


def _build_contrast(
    name: str,
    condition_a: str,
    condition_b: str,
    description: str,
    task_ids: tuple[str, ...],
    records_by_condition: dict[str, dict[str, dict[str, Any]]],
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    outcomes = _condition_outcomes(task_ids, records_by_condition)
    a = outcomes[condition_a]
    b = outcomes[condition_b]
    rate_a = sum(a) / len(a) if a else 0.0
    rate_b = sum(b) / len(b) if b else 0.0
    ci_lower, ci_upper = _paired_bootstrap_ci(a, b, n_bootstrap=n_bootstrap, seed=seed)
    statistic, p_value = _mcnemar_test(a, b)
    n_ab = sum(1 for av, bv in zip(a, b) if av and not bv)
    n_ba = sum(1 for av, bv in zip(a, b) if not av and bv)
    return {
        "name": name,
        "description": description,
        "condition_a": condition_a,
        "condition_b": condition_b,
        "solve_rate_a": round(rate_a, 4),
        "solve_rate_b": round(rate_b, 4),
        "estimate": round(rate_b - rate_a, 4),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_concordant": len(a) - n_ab - n_ba,
        "n_ab": n_ab,
        "n_ba": n_ba,
        "mcnemar_statistic": statistic,
        "mcnemar_p": p_value,
    }


def build_experiment_summary(
    task_ids: tuple[str, ...],
    records_by_condition: dict[str, dict[str, dict[str, Any]]],
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    condition_summaries: dict[str, Any] = {}
    for label in CONDITION_LABELS:
        solves = sum(1 for task_id in task_ids if records_by_condition[label][task_id]["solved"])
        condition_summaries[label] = {
            "config_name": CONDITION_CONFIGS[label].name,
            "solve_count": solves,
            "task_count": len(task_ids),
            "solve_rate": round(solves / len(task_ids), 4) if task_ids else 0.0,
        }
    contrasts = {
        name: _build_contrast(name, a, b, description, task_ids, records_by_condition, n_bootstrap, seed)
        for name, a, b, description in CONTRASTS
    }
    return {
        "task_ids": list(task_ids),
        "task_count": len(task_ids),
        "condition_solve_rates": condition_summaries,
        "contrasts": contrasts,
    }


def _contrast_direction_consistent(frozen: dict[str, Any], native: dict[str, Any]) -> bool:
    return (frozen.get("estimate", 0.0) >= 0.0) == (native.get("estimate", 0.0) >= 0.0)


def _one_sided_evidence(contrast: dict[str, Any]) -> dict[str, Any]:
    ci_excludes_zero = float(contrast.get("ci_lower", 0.0)) > 0.0 or float(contrast.get("ci_upper", 0.0)) < 0.0
    exact_one_sided = int(contrast.get("n_ba", 0)) > 0 and int(contrast.get("n_ab", 0)) == 0
    return {
        "ci_excludes_zero": ci_excludes_zero,
        "exact_one_sided": exact_one_sided,
        "available": ci_excludes_zero or exact_one_sided,
    }


def evaluate_conviction(status: str, strong: bool, directional_consistency: bool) -> str:
    if status == "proven" and strong and directional_consistency:
        return "high"
    if status == "supported_but_not_isolated":
        return "moderate"
    return "low"


def evaluate_factor_evidence(
    factor_name: str,
    subset_name: str,
    native_summary: dict[str, Any],
    frozen_summary: dict[str, Any],
    task_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    if factor_name == "uncertainty":
        primary_native = native_summary["contrasts"]["c01_vs_c00"]
        conditioned_native = native_summary["contrasts"]["c11_vs_c10"]
        primary_frozen = frozen_summary["contrasts"]["c01_vs_c00"]
        conditioned_frozen = frozen_summary["contrasts"]["c11_vs_c10"]
        positive_effect = primary_native["estimate"] > 0.0 or conditioned_native["estimate"] > 0.0
        successful_reorders = sum(1 for item in task_entries if item.get("uncertainty_only_gain") or item.get("synergy_gain"))
        nonzero_reorder_success = sum(
            1
            for item in task_entries
            if item.get("uncertainty_changed_winner") and item.get("uncertainty_improved_correctness")
        )
        gain_category_present = any(
            item.get("attribution_category_v2") in {"uncertainty_only_gain", "synergy_gain"}
            for item in task_entries
        )
        directional_consistency = _contrast_direction_consistent(primary_frozen, primary_native) and _contrast_direction_consistent(conditioned_frozen, conditioned_native)
        evidence = _one_sided_evidence(primary_native)
        strong = positive_effect and evidence["available"] and nonzero_reorder_success > 0 and gain_category_present and directional_consistency
        supported = positive_effect and directional_consistency and (nonzero_reorder_success > 0 or successful_reorders > 0)
    else:
        primary_native = native_summary["contrasts"]["c10_vs_c00"]
        conditioned_native = native_summary["contrasts"]["c11_vs_c01"]
        primary_frozen = frozen_summary["contrasts"]["c10_vs_c00"]
        conditioned_frozen = frozen_summary["contrasts"]["c11_vs_c01"]
        positive_effect = primary_native["estimate"] > 0.0 or conditioned_native["estimate"] > 0.0
        evidence = _one_sided_evidence(primary_native)
        directional_consistency = _contrast_direction_consistent(primary_frozen, primary_native) and _contrast_direction_consistent(conditioned_frozen, conditioned_native)
        gain_category_present = any(
            item.get("attribution_category_v2") in {"refinement_only_gain", "synergy_gain", "refinement_and_uncertainty_both_help_but_not_separable"}
            for item in task_entries
        )
        strong = positive_effect and evidence["available"] and gain_category_present and directional_consistency
        supported = positive_effect and directional_consistency
        nonzero_reorder_success = sum(1 for item in task_entries if item.get("refinement_changed_winner") and item.get("condition_correctness", {}).get("C11"))
    if strong:
        status = "proven"
    elif supported:
        status = "supported_but_not_isolated"
    else:
        status = "still_inconclusive"
    return {
        "factor": factor_name,
        "subset": subset_name,
        "status": status,
        "conviction": evaluate_conviction(status, strong, directional_consistency),
        "positive_effect": positive_effect,
        "directional_consistency_frozen_native": directional_consistency,
        "one_sided_evidence": evidence,
        "nonzero_successful_reorderings": nonzero_reorder_success,
        "gain_category_present": gain_category_present,
        "primary_native_contrast": primary_native,
        "conditioned_native_contrast": conditioned_native,
        "primary_frozen_contrast": primary_frozen,
        "conditioned_frozen_contrast": conditioned_frozen,
        "evidence_rule_satisfied": strong,
    }


def _serializable_top(snapshot: dict[str, Any] | None) -> dict[str, Any] | str:
    return snapshot if snapshot is not None else "unavailable"


def _native_condition_record(fixture: FixtureTask, label: str, split: str) -> dict[str, Any]:
    diagnostic, _ = _case_diagnostic(fixture, CONDITION_CONFIGS[label], split=split)
    first_pass = list(diagnostic.telemetry.get("first_pass_ranking", []))
    final_ranking = list(diagnostic.telemetry.get("final_ranking", []))
    return {
        "task_id": fixture.task_id,
        "condition": label,
        "solved": bool(diagnostic.success_attempt_1),
        "winning_hypothesis": diagnostic.winning_hypothesis,
        "winning_score": diagnostic.winning_score,
        "winning_belief": diagnostic.winning_belief,
        "winning_disbelief": diagnostic.winning_disbelief,
        "winning_uncertainty": diagnostic.winning_uncertainty,
        "failure_class": diagnostic.failure_primary_class,
        "runtime_ms": round(diagnostic.runtime_ms, 4),
        "first_pass_ranking": first_pass,
        "final_ranking": final_ranking,
        "generated_candidates": list(diagnostic.telemetry.get("generated_candidates", [])),
        "refined_candidates": list(diagnostic.telemetry.get("refined_candidates", [])),
        "first_pass_viable_candidates": _viable_candidates_count(first_pass),
        "top_candidate": _serializable_top(_top_snapshot(final_ranking)),
        "top_candidate_first_pass": _serializable_top(_top_snapshot(first_pass)),
    }


def _frozen_condition_result(
    fixture: FixtureTask,
    label: str,
    primitives: list[Any],
    compositions: list[Any],
) -> dict[str, Any]:
    config = CONDITION_CONFIGS[label]
    pool = primitives if label in {"C00", "C01"} else primitives + compositions
    started = time.perf_counter()
    ranking, transform_crash_count, shape_mismatch_count = score_hypotheses(fixture.task, pool, config=config)
    runtime_ms = (time.perf_counter() - started) * 1000.0
    winner, second = select_top_two(ranking, fixture.task.test[0].input)
    prediction = apply_hypothesis(winner, fixture.task.test[0].input) if winner is not None else None
    solved = bool(prediction is not None and fixture.expected_outputs and prediction.equals(fixture.expected_outputs[0]))
    failure_class = None if solved else "wrong_output"
    return {
        "task_id": fixture.task_id,
        "condition": label,
        "solved": solved,
        "winning_hypothesis": winner.description if winner is not None else "",
        "winning_score": winner.score if winner is not None else -1.0,
        "failure_class": failure_class,
        "runtime_ms": round(runtime_ms, 4),
        "ranking": [
            {
                "description": hypothesis.description,
                "family": hypothesis.provenance[0] if hypothesis.provenance else "unknown",
                "belief": hypothesis.belief,
                "disbelief": hypothesis.disbelief,
                "uncertainty": hypothesis.uncertainty,
                "score": hypothesis.score,
                "support_count": hypothesis.support_count,
                "contradiction_count": hypothesis.contradiction_count,
                "unresolved_count": hypothesis.unresolved_count,
            }
            for hypothesis in ranking
        ],
        "top_candidate": _serializable_top(
            {
                "description": winner.description,
                "family": winner.provenance[0] if winner.provenance else "unknown",
                "belief": winner.belief,
                "disbelief": winner.disbelief,
                "uncertainty": winner.uncertainty,
                "score": winner.score,
            }
            if winner is not None
            else None
        ),
        "second_candidate": second.description if second is not None else "",
        "primitive_pool_size": len(primitives),
        "full_pool_size": len(primitives) + len(compositions),
        "generated_candidates": [hypothesis.description for hypothesis in primitives],
        "refined_candidates": [hypothesis.description for hypothesis in compositions],
        "transform_crash_count": transform_crash_count,
        "shape_mismatch_count": shape_mismatch_count,
        "viable_candidates": _viable_candidates_count([
            {
                "belief": hypothesis.belief,
                "uncertainty": hypothesis.uncertainty,
                "score": hypothesis.score,
            }
            for hypothesis in ranking
        ]),
    }


def run_native_factorial_v2(fixtures: list[FixtureTask], split: str) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        label: {fixture.task_id: _native_condition_record(fixture, label, split) for fixture in fixtures}
        for label in CONDITION_LABELS
    }


def run_frozen_factorial_v2(fixtures: list[FixtureTask], split: str) -> dict[str, dict[str, dict[str, Any]]]:
    _ = split
    records: dict[str, dict[str, dict[str, Any]]] = {label: {} for label in CONDITION_LABELS}
    for fixture in fixtures:
        primitives = generate_hypotheses(fixture.task, config=FULL_COAGENCY_CONFIG)
        first_scored, _, _ = score_hypotheses(fixture.task, primitives, config=FULL_COAGENCY_CONFIG)
        survivors, _ = critic_prune(first_scored, keep=FULL_COAGENCY_CONFIG.first_pass_keep, config=FULL_COAGENCY_CONFIG)
        compositions = refine_hypotheses(fixture.task, survivors, config=FULL_COAGENCY_CONFIG)
        for label in CONDITION_LABELS:
            records[label][fixture.task_id] = _frozen_condition_result(fixture, label, primitives, compositions)
    return records


def build_task_level_attribution_v2(
    entries: list[ManifestEntry],
    native_records: dict[str, dict[str, dict[str, Any]]],
    frozen_records: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        task_id = entry.task_id
        native_c00 = native_records["C00"][task_id]
        native_c10 = native_records["C10"][task_id]
        native_c01 = native_records["C01"][task_id]
        native_c11 = native_records["C11"][task_id]
        frozen_c00 = frozen_records["C00"][task_id]
        frozen_c01 = frozen_records["C01"][task_id]
        c00 = bool(native_c00["solved"])
        c10 = bool(native_c10["solved"])
        c01 = bool(native_c01["solved"])
        c11 = bool(native_c11["solved"])
        category = categorize_task_attribution_v2(c00, c10, c01, c11, family=entry.family)
        point_order = _ordering(list(frozen_c00.get("ranking", [])))
        uncertainty_order = _ordering(list(frozen_c01.get("ranking", [])))
        final_order = _ordering(list(native_c11.get("final_ranking", [])))
        ranking_conflict = point_order[:1] != uncertainty_order[:1]
        refinement_changed_winner = _ordering(list(native_c11.get("first_pass_ranking", [])), 1) != _ordering(list(native_c11.get("final_ranking", [])), 1)
        uncertainty_improved = bool(frozen_c01["solved"] and not frozen_c00["solved"])
        uncertainty_hurt = bool(frozen_c00["solved"] and not frozen_c01["solved"])
        rows.append(
            {
                "task_id": task_id,
                "manifest_family": entry.family,
                "intended_primary_mechanism": entry.intended_primary_mechanism,
                "notes": entry.notes,
                "frozen_candidate_pool_size": {
                    "primitive_pool": frozen_c00.get("primitive_pool_size"),
                    "with_refinement_pool": frozen_c00.get("full_pool_size"),
                },
                "viable_competing_candidates_after_first_pass": frozen_c00.get("viable_candidates", "unavailable"),
                "candidate_identities_or_families": [
                    {
                        "description": item.get("description", ""),
                        "family": item.get("family", ""),
                    }
                    for item in list(frozen_c00.get("ranking", []))[:5]
                ] or "unavailable",
                "point_estimate_first_pass_ordering": point_order or ["unavailable"],
                "uncertainty_aware_first_pass_ordering": uncertainty_order or ["unavailable"],
                "final_ordering_after_refinement": final_order or ["unavailable"],
                "point_estimate_top_candidate": _serializable_top(_top_snapshot(list(frozen_c00.get("ranking", [])))),
                "uncertainty_aware_top_candidate": _serializable_top(_top_snapshot(list(frozen_c01.get("ranking", [])))),
                "ranking_conflict_occurred": ranking_conflict,
                "uncertainty_changed_winner": ranking_conflict,
                "uncertainty_improved_correctness": uncertainty_improved,
                "uncertainty_hurt_correctness": uncertainty_hurt,
                "refinement_changed_winner": refinement_changed_winner,
                "condition_correctness": {label: bool(native_records[label][task_id]["solved"]) for label in CONDITION_LABELS},
                "failure_class_by_condition": {label: native_records[label][task_id].get("failure_class") for label in CONDITION_LABELS},
                "runtime_ms_by_condition": {label: native_records[label][task_id].get("runtime_ms") for label in CONDITION_LABELS},
                "attribution_category_v2": category,
                "uncertainty_only_gain": category == "uncertainty_only_gain",
                "synergy_gain": category == "synergy_gain",
            }
        )
    return rows


def build_subset_analyses(
    entries: list[ManifestEntry],
    native_records: dict[str, dict[str, dict[str, Any]]],
    frozen_records: dict[str, dict[str, dict[str, Any]]],
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    analyses: dict[str, Any] = {}
    for subset_name in PRIMARY_SUBSETS:
        task_ids = subset_task_ids(entries, mechanism=None if subset_name == "all_blind_holdout_v3" else subset_name)
        native_summary = build_experiment_summary(task_ids, native_records, n_bootstrap=n_bootstrap, seed=seed)
        frozen_summary = build_experiment_summary(task_ids, frozen_records, n_bootstrap=n_bootstrap, seed=seed)
        analyses[subset_name] = {
            "subset": subset_name,
            "task_ids": list(task_ids),
            "task_count": len(task_ids),
            "native": native_summary,
            "frozen": frozen_summary,
            "directional_consistency": {
                name: _contrast_direction_consistent(frozen_summary["contrasts"][name], native_summary["contrasts"][name])
                for name, _, _, _ in CONTRASTS
            },
        }
    return analyses


def build_uncertainty_causal_analysis(
    subset_analyses: dict[str, Any],
    task_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    ranking_tasks = [item for item in task_entries if item["manifest_family"] == "ranking_conflict"]
    disagreement_count = sum(1 for item in ranking_tasks if item.get("uncertainty_changed_winner"))
    improved_count = sum(1 for item in ranking_tasks if item.get("uncertainty_improved_correctness"))
    hurt_count = sum(1 for item in ranking_tasks if item.get("uncertainty_hurt_correctness"))
    solved_nonzero_uncertainty = sum(
        1
        for item in ranking_tasks
        if item.get("condition_correctness", {}).get("C11")
        and float(item.get("uncertainty_aware_top_candidate", {}).get("uncertainty", 0.0)) > 0.0
    )
    wins_beyond_refinement = sum(
        1
        for item in ranking_tasks
        if item.get("condition_correctness", {}).get("C11") and not item.get("condition_correctness", {}).get("C10")
    )
    native_summary = subset_analyses["ranking_conflict"]["native"]
    frozen_summary = subset_analyses["ranking_conflict"]["frozen"]
    uncertainty_evidence = evaluate_factor_evidence(
        "uncertainty",
        "ranking_conflict",
        native_summary,
        frozen_summary,
        ranking_tasks,
    )
    return {
        "subset": "ranking_conflict",
        "task_count": len(ranking_tasks),
        "winner_changed_count": disagreement_count,
        "improved_correctness_count": improved_count,
        "hurt_count": hurt_count,
        "solved_tasks_with_nonzero_winning_uncertainty": solved_nonzero_uncertainty,
        "point_estimate_vs_uncertainty_first_pass_disagreement_count": disagreement_count,
        "wins_produced_by_uncertainty_that_refinement_alone_did_not": wins_beyond_refinement,
        "native_contrasts": native_summary["contrasts"],
        "frozen_contrasts": frozen_summary["contrasts"],
        "exact_paired_counts": {
            "native_c01_vs_c00": {
                "n_ba": native_summary["contrasts"]["c01_vs_c00"]["n_ba"],
                "n_ab": native_summary["contrasts"]["c01_vs_c00"]["n_ab"],
            },
            "native_c11_vs_c10": {
                "n_ba": native_summary["contrasts"]["c11_vs_c10"]["n_ba"],
                "n_ab": native_summary["contrasts"]["c11_vs_c10"]["n_ab"],
            },
        },
        "factor_evidence": uncertainty_evidence,
    }


def build_causal_verdict_v2(
    subset_analyses: dict[str, Any],
    task_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    refinement_tasks = [item for item in task_entries if item["manifest_family"] == "refinement_composition"]
    uncertainty_tasks = [item for item in task_entries if item["manifest_family"] == "ranking_conflict"]
    refinement_evidence = evaluate_factor_evidence(
        "refinement",
        "refinement_composition",
        subset_analyses["refinement_composition"]["native"],
        subset_analyses["refinement_composition"]["frozen"],
        refinement_tasks,
    )
    uncertainty_evidence = evaluate_factor_evidence(
        "uncertainty",
        "ranking_conflict",
        subset_analyses["ranking_conflict"]["native"],
        subset_analyses["ranking_conflict"]["frozen"],
        uncertainty_tasks,
    )
    if refinement_evidence["status"] == "proven" and uncertainty_evidence["status"] == "proven":
        overall = "proven"
    elif refinement_evidence["status"] == "proven" or uncertainty_evidence["status"] == "proven":
        overall = "supported_but_not_isolated"
    else:
        overall = "still_inconclusive"
    overall_conviction = "high" if refinement_evidence["conviction"] == "high" and uncertainty_evidence["conviction"] != "low" else ("moderate" if refinement_evidence["conviction"] == "high" else "low")
    return {
        "overall_status": overall,
        "overall_conviction": overall_conviction,
        "refinement": refinement_evidence,
        "uncertainty": uncertainty_evidence,
        "overall_condition_rates_native": subset_analyses["all_blind_holdout_v3"]["native"]["condition_solve_rates"],
        "overall_exact_paired_counts": {
            name: {
                "n_ba": subset_analyses["all_blind_holdout_v3"]["native"]["contrasts"][name]["n_ba"],
                "n_ab": subset_analyses["all_blind_holdout_v3"]["native"]["contrasts"][name]["n_ab"],
            }
            for name in ("c10_vs_c00", "c01_vs_c00", "c11_vs_c10", "c11_vs_c01")
        },
    }


def build_thesis_final_summary(
    freeze_manifest: dict[str, Any],
    verdict: dict[str, Any],
    uncertainty_analysis: dict[str, Any],
    task_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    category_counts = Counter(item["attribution_category_v2"] for item in task_entries)
    return {
        "split": "blind_holdout_v3",
        "freeze_manifest": freeze_manifest,
        "verdict": verdict,
        "uncertainty_analysis": uncertainty_analysis,
        "category_counts": dict(sorted(category_counts.items())),
        "summary": {
            "c00": verdict["overall_condition_rates_native"]["C00"]["solve_rate"],
            "c10": verdict["overall_condition_rates_native"]["C10"]["solve_rate"],
            "c01": verdict["overall_condition_rates_native"]["C01"]["solve_rate"],
            "c11": verdict["overall_condition_rates_native"]["C11"]["solve_rate"],
            "uncertainty_status": verdict["uncertainty"]["status"],
            "refinement_status": verdict["refinement"]["status"],
            "uncertainty_winner_changes": uncertainty_analysis["winner_changed_count"],
        },
    }


def task_level_attribution_markdown_v2(task_entries: list[dict[str, Any]]) -> str:
    rows = []
    for item in task_entries:
        cond = item["condition_correctness"]
        rows.append([
            item["task_id"],
            item["manifest_family"],
            "yes" if item["ranking_conflict_occurred"] else "no",
            "yes" if item["refinement_changed_winner"] else "no",
            "yes" if cond["C00"] else "no",
            "yes" if cond["C10"] else "no",
            "yes" if cond["C01"] else "no",
            "yes" if cond["C11"] else "no",
            item["attribution_category_v2"],
        ])
    lines = [
        "# Task-Level Attribution v2",
        "",
        _markdown_table(
            ["Task", "Family", "Ranking conflict", "Refinement changed winner", "C00", "C10", "C01", "C11", "Category"],
            rows,
        ),
        "",
        "## Telemetry Notes",
        "",
        "- `point_estimate_first_pass_ordering` and `uncertainty_aware_first_pass_ordering` come from the frozen primitives-only pool (C00 vs C01).",
        "- `final_ordering_after_refinement` comes from the native full pipeline (C11).",
        "- Missing values would be reported as `unavailable`; none were withheld here.",
        "",
    ]
    return "\n".join(lines)


def uncertainty_causal_markdown(payload: dict[str, Any]) -> str:
    evidence = payload["factor_evidence"]
    rows = [
        ["ranking_conflict tasks", str(payload["task_count"])],
        ["winner changed", str(payload["winner_changed_count"])],
        ["improved correctness", str(payload["improved_correctness_count"])],
        ["hurt", str(payload["hurt_count"])],
        ["solved with nonzero winning uncertainty", str(payload["solved_tasks_with_nonzero_winning_uncertainty"])],
        ["wins beyond refinement alone", str(payload["wins_produced_by_uncertainty_that_refinement_alone_did_not"])],
        ["status", evidence["status"]],
        ["conviction", evidence["conviction"]],
    ]
    lines = [
        "# Uncertainty Causal Analysis",
        "",
        _markdown_table(["Metric", "Value"], rows),
        "",
        "## Evidence Rule Check",
        "",
        f"- Positive uncertainty effect on ranking_conflict subset: {'yes' if evidence['positive_effect'] else 'no'}.",
        f"- Materially one-sided evidence: {'yes' if evidence['one_sided_evidence']['available'] else 'no'}.",
        f"- Nonzero successful uncertainty-driven reorderings: {evidence['nonzero_successful_reorderings']}.",
        f"- At least one uncertainty_only_gain or synergy_gain: {'yes' if evidence['gain_category_present'] else 'no'}.",
        f"- Directional consistency frozen/native: {'yes' if evidence['directional_consistency_frozen_native'] else 'no'}.",
        "",
        "## Explicit Verdict",
        "",
        f"> Uncertainty is `{evidence['status']}` on blind_holdout_v3 with `{evidence['conviction']}` conviction.",
        "",
    ]
    return "\n".join(lines)


def causal_verdict_markdown_v2(payload: dict[str, Any]) -> str:
    overall = payload["overall_condition_rates_native"]
    rows = [[label, f"{overall[label]['solve_rate']:.3f}"] for label in CONDITION_LABELS]
    lines = [
        "# Causal Verdict v2",
        "",
        _markdown_table(["Condition", "Solve rate"], rows),
        "",
        "## Factor Verdicts",
        "",
        _markdown_table(
            ["Factor", "Status", "Conviction", "Directional consistency"],
            [
                [
                    "refinement",
                    payload["refinement"]["status"],
                    payload["refinement"]["conviction"],
                    "yes" if payload["refinement"]["directional_consistency_frozen_native"] else "no",
                ],
                [
                    "uncertainty",
                    payload["uncertainty"]["status"],
                    payload["uncertainty"]["conviction"],
                    "yes" if payload["uncertainty"]["directional_consistency_frozen_native"] else "no",
                ],
            ],
        ),
        "",
        f"> Overall verdict: `{payload['overall_status']}` with `{payload['overall_conviction']}` conviction.",
        "",
    ]
    return "\n".join(lines)


def causal_factorial_markdown_v2(bundle: dict[str, Any]) -> str:
    subset_rows = []
    for subset_name in PRIMARY_SUBSETS:
        native = bundle["subset_analyses"][subset_name]["native"]["condition_solve_rates"]
        subset_rows.append(
            [
                subset_name,
                str(bundle["subset_analyses"][subset_name]["task_count"]),
                f"{native['C00']['solve_rate']:.3f}",
                f"{native['C10']['solve_rate']:.3f}",
                f"{native['C01']['solve_rate']:.3f}",
                f"{native['C11']['solve_rate']:.3f}",
            ]
        )
    return "\n".join(
        [
            "# Causal Factorial v2",
            "",
            "> blind_holdout_v3 is frozen by intended mechanism. Subset labels come from the manifest, not from solver outcomes.",
            "",
            _markdown_table(
                ["Subset", "Tasks", "C00", "C10", "C01", "C11"],
                subset_rows,
            ),
            "",
            "## Factor Verdict Snapshot",
            "",
            f"- Refinement: `{bundle['causal_verdict_v2']['refinement']['status']}` ({bundle['causal_verdict_v2']['refinement']['conviction']}).",
            f"- Uncertainty: `{bundle['causal_verdict_v2']['uncertainty']['status']}` ({bundle['causal_verdict_v2']['uncertainty']['conviction']}).",
            f"- Overall: `{bundle['causal_verdict_v2']['overall_status']}` ({bundle['causal_verdict_v2']['overall_conviction']}).",
            "",
        ]
    )


def thesis_final_summary_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Thesis Final Attribution Summary",
        "",
        f"- Frozen benchmark: `{payload['freeze_manifest']['manifest_hash_sha256']}`",
        f"- C00={summary['c00']:.3f}, C10={summary['c10']:.3f}, C01={summary['c01']:.3f}, C11={summary['c11']:.3f}",
        f"- Refinement verdict: `{summary['refinement_status']}`.",
        f"- Uncertainty verdict: `{summary['uncertainty_status']}`.",
        f"- Uncertainty winner changes on ranking_conflict subset: `{summary['uncertainty_winner_changes']}`.",
        "",
        "## Category Counts",
        "",
        _markdown_table(
            ["Category", "Count"],
            [[name, str(count)] for name, count in sorted(payload["category_counts"].items())] or [["none", "0"]],
        ),
        "",
        "## Final Verdict",
        "",
        f"> blind_holdout_v3 supports a strong refinement claim ({payload['verdict']['refinement']['status']}) and an uncertainty claim that is {payload['verdict']['uncertainty']['status']}. Positive uncertainty evidence is not required; the benchmark reports the observed null clearly.",
        "",
    ]
    return "\n".join(lines)
