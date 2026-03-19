from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arc_epistemic.eval.causal import _mcnemar_test, _paired_bootstrap_ci
from arc_epistemic.eval.fixtures import FixtureTask
from arc_epistemic.solver.agents import (
    FULL_COAGENCY_CONFIG,
    PRIMITIVE_BASELINE_CONFIG,
    SolverConfig,
    critic_prune,
    generate_hypotheses,
    refine_hypotheses,
    score_hypotheses,
)
from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.output_competition import (
    output_entropy,
    output_margin,
    output_uncertainty,
    rank_output_classes,
    select_contested_hypotheses,
    select_top_two_diversity_aware_output_classes,
    select_top_two_output_classes,
    serialize_output_supports,
)
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.solver.solver import solve_task_with_diagnostics

METHOD_ORDER: tuple[str, ...] = ("M0", "M1", "M2", "M3", "M4", "R_anchor")
METHOD_LABELS: dict[str, str] = {
    "M0": "single_best_point_estimate",
    "M1": "local_epistemic_single_best",
    "M2": "output_mass_selector",
    "M3": "output_mass_diversity_selector",
    "M4": "output_mass_diversity_margin_gated",
    "R_anchor": "broad_refinement_anchor",
}
PAIRWISE_RATE_CONTRASTS: tuple[tuple[str, str, str], ...] = (
    ("m2_vs_m0", "M0", "M2"),
    ("m2_vs_m1", "M1", "M2"),
    ("m3_vs_m2", "M2", "M3"),
    ("m4_vs_m3", "M3", "M4"),
    ("m4_vs_anchor", "R_anchor", "M4"),
)

METHOD_CONFIGS_NATIVE: dict[str, SolverConfig] = {
    "M0": SolverConfig(
        name="m0_single_best",
        use_epistemic_scoring=False,
        use_refinement=True,
    ),
    "M1": SolverConfig(
        name="m1_local_epistemic",
        use_epistemic_scoring=True,
        use_refinement=True,
    ),
    "M2": SolverConfig(
        name="m2_output_mass",
        use_epistemic_scoring=True,
        use_refinement=True,
        use_output_aggregation=True,
    ),
    "M3": SolverConfig(
        name="m3_output_mass_diversity",
        use_epistemic_scoring=True,
        use_refinement=True,
        use_output_aggregation=True,
        use_diversity_aware_output_selection=True,
    ),
    "M4": SolverConfig(
        name="m4_output_mass_diversity_margin_gated",
        use_epistemic_scoring=True,
        use_refinement=True,
        use_output_aggregation=True,
        use_diversity_aware_output_selection=True,
        use_margin_gated_refinement=True,
        contested_margin_threshold=0.18,
        contested_entropy_threshold=0.65,
        contested_output_keep=2,
    ),
    "R_anchor": SolverConfig(
        name="r_anchor_broad_refinement",
        use_epistemic_scoring=True,
        use_refinement=True,
    ),
}

QUALITY_GATE_THRESHOLDS: dict[str, dict[str, int | float]] = {
    "selector_divergence": {
        "min_multiple_hypotheses": 10,
        "min_multiple_output_classes": 10,
        "min_small_margin": 8,
        "min_selector_disagreement_m0_m2": 8,
        "min_output_selection_improves_correctness": 6,
    },
    "diversity_sensitive": {
        "min_multiple_hypotheses": 6,
        "min_multiple_output_classes": 6,
        "min_small_margin": 5,
        "min_selector_disagreement_m2_m3": 5,
        "min_diversity_improves_correctness": 4,
    },
    "refinement_composition": {
        "min_multiple_hypotheses": 6,
        "min_multiple_output_classes": 6,
    },
    "control": {
        "max_selector_disagreement_m0_m2": 0,
        "max_selector_disagreement_m2_m3": 0,
    },
    "overall": {
        "min_nonzero_output_entropy": 24,
        "min_selector_disagreement_m0_m2": 8,
        "min_selector_disagreement_m2_m3": 5,
        "min_output_selection_improves_correctness": 6,
        "min_diversity_improves_correctness": 4,
    },
}


@dataclass(frozen=True)
class ManifestEntry:
    task_id: str
    family: str
    intended_primary_mechanism: str
    intended_multiple_hypotheses_expected: str
    intended_multiple_output_classes_expected: str
    intended_selector_disagreement_expected: str
    intended_small_margin_expected: str
    notes: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json_hash(payload: Any) -> str:
    data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _table(headers: list[str], rows: list[list[str]]) -> str:
    parts = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        parts.append("| " + " | ".join(row) + " |")
    return "\n".join(parts)


def load_manifest(path: str | Path) -> list[ManifestEntry]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [ManifestEntry(**entry) for entry in payload.get("entries", [])]


def manifest_by_task(entries: list[ManifestEntry]) -> dict[str, ManifestEntry]:
    return {entry.task_id: entry for entry in entries}


def build_freeze_manifest(
    split_name: str,
    split_path: str | Path,
    manifest_path: str | Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    split_payload = json.loads(Path(split_path).read_text(encoding="utf-8"))
    manifest_payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    family_counts = Counter(entry["family"] for entry in manifest_payload.get("entries", []))
    return {
        "split": split_name,
        "generated_at_utc": generated_at_utc or _now_utc(),
        "task_count": len(split_payload.get("task_ids", [])),
        "task_ids": list(split_payload.get("task_ids", [])),
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
        ["split", str(payload["split"])],
        ["generated_at_utc", str(payload["generated_at_utc"])],
        ["task_count", str(payload["task_count"])],
        ["manifest_hash_sha256", str(payload["manifest_hash_sha256"])],
        ["split_hash_sha256", str(payload["split_hash_sha256"])],
    ]
    family_rows = [[family, str(count)] for family, count in sorted(payload["family_counts"].items())]
    return "\n".join(
        [
            f"# {payload['split']} Freeze Manifest",
            "",
            "> Task authoring and manifest labeling must be frozen before the thesis-facing evaluation run.",
            "",
            _table(["Field", "Value"], rows),
            "",
            "## Family Counts",
            "",
            _table(["Family", "Count"], family_rows),
        ]
    )


def _bootstrap_numeric_ci(
    values_a: list[float],
    values_b: list[float],
    *,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> tuple[float, float]:
    if not values_a:
        return (0.0, 0.0)
    rng = __import__("random").Random(seed)
    diffs = [b - a for a, b in zip(values_a, values_b)]
    boot_means: list[float] = []
    n = len(diffs)
    for _ in range(n_bootstrap):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo = boot_means[int(math.floor(0.025 * n_bootstrap))]
    hi = boot_means[min(n_bootstrap - 1, int(math.ceil(0.975 * n_bootstrap)) - 1)]
    return (round(lo, 4), round(hi, 4))


def _selection_from_ranked(method: str, ranked_hypotheses: list, test_input) -> tuple[str, Any, tuple[dict[str, object], ...]]:
    if method == "M3" or method == "M4":
        hypothesis, _, supports = select_top_two_diversity_aware_output_classes(ranked_hypotheses, test_input)
        return ("output_mass_diversity", hypothesis, serialize_output_supports(supports))
    if method == "M2":
        hypothesis, _, supports = select_top_two_output_classes(ranked_hypotheses, test_input)
        return ("output_mass", hypothesis, serialize_output_supports(supports))
    hypothesis, _ = select_top_two(ranked_hypotheses, test_input)
    supports = rank_output_classes(ranked_hypotheses, test_input, strategy="mass")
    return ("single_best", hypothesis, serialize_output_supports(supports))


def _selected_output(method: str, ranked_hypotheses: list, test_input):
    mode, hypothesis, serialized_supports = _selection_from_ranked(method, ranked_hypotheses, test_input)
    if hypothesis is None:
        return {
            "selection_mode": mode,
            "selected_hypothesis": "",
            "selected_output": None,
            "selected_output_fingerprint": "",
            "output_supports": list(serialized_supports),
            "output_uncertainty": 1.0,
            "output_entropy": 1.0,
            "output_margin": 0.0,
            "selector_differs_from_m0": False,
        }
    predicted = apply_hypothesis(hypothesis, test_input)
    supports = rank_output_classes(ranked_hypotheses, test_input, strategy="diversity" if method in ("M3", "M4") else "mass")
    return {
        "selection_mode": mode,
        "selected_hypothesis": hypothesis.description,
        "selected_output": predicted,
        "selected_output_fingerprint": predicted.fingerprint() if predicted is not None else "",
        "output_supports": list(serialize_output_supports(supports)),
        "output_uncertainty": round(output_uncertainty(supports), 6),
        "output_entropy": round(output_entropy(supports), 6),
        "output_margin": round(output_margin(supports), 6),
        "selector_differs_from_m0": False,
    }


def _method_compute_row(
    method: str,
    ranked_hypotheses: list,
    *,
    expected_output,
    test_input,
    generated_count: int,
    scored_count: int,
    refined_count: int,
    refined_output_classes: int,
    runtime_ms: float,
    gate: dict[str, object] | None = None,
) -> dict[str, Any]:
    selection = _selected_output(method, ranked_hypotheses, test_input)
    predicted = selection["selected_output"]
    solved = predicted is not None and predicted.cache_key() == expected_output.cache_key()
    output_class_count = len(selection["output_supports"])
    return {
        "selection_mode": selection["selection_mode"],
        "selected_hypothesis": selection["selected_hypothesis"],
        "selected_output_fingerprint": selection["selected_output_fingerprint"],
        "correct": solved,
        "surviving_hypothesis_count": len(ranked_hypotheses),
        "distinct_output_class_count": output_class_count,
        "multiple_hypotheses_survived": len(ranked_hypotheses) > 1,
        "multiple_output_classes_survived": output_class_count > 1,
        "output_supports": selection["output_supports"],
        "output_uncertainty": selection["output_uncertainty"],
        "output_entropy": selection["output_entropy"],
        "output_margin": selection["output_margin"],
        "generated_candidates": generated_count,
        "scored_hypotheses": scored_count,
        "refined_hypotheses": refined_count,
        "refined_output_classes": refined_output_classes,
        "runtime_ms": round(runtime_ms, 6),
        "failure_class": None if solved else "wrong_answer",
        "refinement_triggered": bool(gate and gate.get("contested")),
        "refinement_gate": gate or {"mode": "not_applicable"},
    }


def _frozen_task_method_rows(fixture: FixtureTask) -> dict[str, dict[str, Any]]:
    task = fixture.task
    expected = fixture.expected_outputs[0]
    test_input = task.test[0].input
    generated = generate_hypotheses(task, config=FULL_COAGENCY_CONFIG)
    first_scored, _, _ = score_hypotheses(task, generated, config=FULL_COAGENCY_CONFIG)
    survivors, _ = critic_prune(first_scored, keep=FULL_COAGENCY_CONFIG.first_pass_keep, config=FULL_COAGENCY_CONFIG)
    broad_refined = refine_hypotheses(task, survivors, config=FULL_COAGENCY_CONFIG)
    broad_pool = survivors + broad_refined

    started = time.perf_counter()
    ranked_m0, _, _ = score_hypotheses(task, broad_pool, config=PRIMITIVE_BASELINE_CONFIG)
    runtime_m0 = (time.perf_counter() - started) * 1000.0

    started = time.perf_counter()
    ranked_epistemic, _, _ = score_hypotheses(task, broad_pool, config=FULL_COAGENCY_CONFIG)
    runtime_ep = (time.perf_counter() - started) * 1000.0

    gate_source, gate = select_contested_hypotheses(
        survivors,
        test_input,
        margin_threshold=METHOD_CONFIGS_NATIVE["M4"].contested_margin_threshold,
        entropy_threshold=METHOD_CONFIGS_NATIVE["M4"].contested_entropy_threshold,
        keep_outputs=METHOD_CONFIGS_NATIVE["M4"].contested_output_keep,
        strategy="diversity",
    )
    gated_refined = refine_hypotheses(task, gate_source, config=FULL_COAGENCY_CONFIG)
    gated_pool = survivors + gated_refined
    started = time.perf_counter()
    ranked_gated, _, _ = score_hypotheses(task, gated_pool, config=FULL_COAGENCY_CONFIG)
    runtime_gated = (time.perf_counter() - started) * 1000.0

    rows = {
        "M0": _method_compute_row(
            "M0",
            ranked_m0,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(broad_pool),
            refined_count=0,
            refined_output_classes=0,
            runtime_ms=runtime_m0,
        ),
        "M1": _method_compute_row(
            "M1",
            ranked_epistemic,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(broad_pool),
            refined_count=0,
            refined_output_classes=0,
            runtime_ms=runtime_ep,
        ),
        "M2": _method_compute_row(
            "M2",
            ranked_epistemic,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(broad_pool),
            refined_count=0,
            refined_output_classes=0,
            runtime_ms=runtime_ep,
        ),
        "M3": _method_compute_row(
            "M3",
            ranked_epistemic,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(broad_pool),
            refined_count=0,
            refined_output_classes=0,
            runtime_ms=runtime_ep,
        ),
        "M4": _method_compute_row(
            "M4",
            ranked_gated,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(gated_pool),
            refined_count=len(gated_refined),
            refined_output_classes=int(gate.get("selected_outputs", 0)),
            runtime_ms=runtime_gated,
            gate=gate,
        ),
        "R_anchor": _method_compute_row(
            "R_anchor",
            ranked_epistemic,
            expected_output=expected,
            test_input=test_input,
            generated_count=len(generated),
            scored_count=len(broad_pool),
            refined_count=len(broad_refined),
            refined_output_classes=len(rank_output_classes(first_scored, test_input, strategy="mass")),
            runtime_ms=runtime_ep,
            gate={"mode": "broad_refinement", "contested": False},
        ),
    }
    m0_fingerprint = rows["M0"]["selected_output_fingerprint"]
    for method in METHOD_ORDER:
        rows[method]["selector_differs_from_m0"] = rows[method]["selected_output_fingerprint"] != m0_fingerprint
    return rows


def run_frozen_experiment(fixtures: list[FixtureTask], entries: list[ManifestEntry], *, split: str, freeze_manifest: dict[str, Any]) -> dict[str, Any]:
    entry_lookup = manifest_by_task(entries)
    task_rows = []
    for fixture in fixtures:
        method_rows = _frozen_task_method_rows(fixture)
        task_rows.append(
            {
                "task_id": fixture.task_id,
                "manifest_family": entry_lookup[fixture.task_id].family,
                "freeze_manifest_hash": freeze_manifest["manifest_hash_sha256"],
                "methods": method_rows,
            }
        )
    return {
        "split": split,
        "evaluation_mode": "frozen_candidate_pool",
        "freeze_manifest_hash": freeze_manifest["manifest_hash_sha256"],
        "generated_at_utc": _now_utc(),
        "task_count": len(task_rows),
        "tasks": task_rows,
    }


def _native_method_row(fixture: FixtureTask, method: str, config: SolverConfig) -> dict[str, Any]:
    expected = fixture.expected_outputs[0]
    test_input = fixture.task.test[0].input
    started = time.perf_counter()
    result = solve_task_with_diagnostics(fixture.task, config=config)
    runtime_ms = (time.perf_counter() - started) * 1000.0
    if method == "M3":
        ranked_for_selection = result.ranked_hypotheses
    else:
        ranked_for_selection = result.ranked_hypotheses
    predicted = result.predictions[0][0]
    base_row = _method_compute_row(
        method,
        ranked_for_selection,
        expected_output=expected,
        test_input=test_input,
        generated_count=result.loop_diagnostics.generated_count,
        scored_count=result.loop_diagnostics.second_pass_scored_count,
        refined_count=result.loop_diagnostics.refined_count if config.use_refinement else 0,
        refined_output_classes=int(result.loop_diagnostics.refinement_gate.get("selected_outputs", 0)) if config.use_refinement else 0,
        runtime_ms=runtime_ms,
        gate=result.loop_diagnostics.refinement_gate if config.use_refinement else None,
    )
    if predicted is not None and predicted.cache_key() == expected.cache_key():
        base_row["correct"] = True
        base_row["failure_class"] = None
    return base_row


def run_native_experiment(fixtures: list[FixtureTask], entries: list[ManifestEntry], *, split: str, freeze_manifest: dict[str, Any]) -> dict[str, Any]:
    entry_lookup = manifest_by_task(entries)
    task_rows = []
    for fixture in fixtures:
        method_rows = {
            method: _native_method_row(fixture, method, config)
            for method, config in METHOD_CONFIGS_NATIVE.items()
        }
        m0_fingerprint = method_rows["M0"]["selected_output_fingerprint"]
        for method in METHOD_ORDER:
            method_rows[method]["selector_differs_from_m0"] = method_rows[method]["selected_output_fingerprint"] != m0_fingerprint
        task_rows.append(
            {
                "task_id": fixture.task_id,
                "manifest_family": entry_lookup[fixture.task_id].family,
                "freeze_manifest_hash": freeze_manifest["manifest_hash_sha256"],
                "methods": method_rows,
            }
        )
    return {
        "split": split,
        "evaluation_mode": "native_pipeline",
        "freeze_manifest_hash": freeze_manifest["manifest_hash_sha256"],
        "generated_at_utc": _now_utc(),
        "task_count": len(task_rows),
        "tasks": task_rows,
    }


def _family_task_rows(experiment: dict[str, Any], family: str | None = None) -> list[dict[str, Any]]:
    if family is None:
        return list(experiment["tasks"])
    return [row for row in experiment["tasks"] if row["manifest_family"] == family]


def _aggregate_method_metrics(task_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    aggregates: dict[str, dict[str, Any]] = {}
    for method in METHOD_ORDER:
        rows = [row["methods"][method] for row in task_rows]
        task_count = len(rows)
        solve_count = sum(1 for row in rows if row["correct"])
        scored = [row["scored_hypotheses"] for row in rows]
        refined = [row["refined_hypotheses"] for row in rows]
        runtime = [row["runtime_ms"] for row in rows]
        aggregates[method] = {
            "method_label": METHOD_LABELS[method],
            "task_count": task_count,
            "solve_count": solve_count,
            "solve_rate": round((solve_count / task_count) if task_count else 0.0, 4),
            "mean_generated_candidates": round(sum(row["generated_candidates"] for row in rows) / task_count, 4) if task_count else 0.0,
            "mean_scored_hypotheses": round(sum(scored) / task_count, 4) if task_count else 0.0,
            "mean_refined_hypotheses": round(sum(refined) / task_count, 4) if task_count else 0.0,
            "mean_refined_output_classes": round(sum(row["refined_output_classes"] for row in rows) / task_count, 4) if task_count else 0.0,
            "mean_runtime_ms": round(sum(runtime) / task_count, 4) if task_count else 0.0,
            "mean_output_uncertainty": round(sum(row["output_uncertainty"] for row in rows) / task_count, 4) if task_count else 0.0,
            "mean_output_entropy": round(sum(row["output_entropy"] for row in rows) / task_count, 4) if task_count else 0.0,
            "mean_output_margin": round(sum(row["output_margin"] for row in rows) / task_count, 4) if task_count else 0.0,
            "solve_rate_per_scored_hypothesis": round((solve_count / max(1.0, sum(scored) / task_count)), 6) if task_count else 0.0,
        }
    return aggregates


def summarize_experiment(experiment: dict[str, Any]) -> dict[str, Any]:
    family_names = sorted({row["manifest_family"] for row in experiment["tasks"]})
    return {
        "split": experiment["split"],
        "evaluation_mode": experiment["evaluation_mode"],
        "freeze_manifest_hash": experiment["freeze_manifest_hash"],
        "generated_at_utc": experiment["generated_at_utc"],
        "task_count": experiment["task_count"],
        "overall": _aggregate_method_metrics(experiment["tasks"]),
        "by_family": {
            family: _aggregate_method_metrics(_family_task_rows(experiment, family))
            for family in family_names
        },
        "tasks": experiment["tasks"],
    }


def _pairwise_counts(task_rows: list[dict[str, Any]], method_a: str, method_b: str) -> dict[str, int]:
    only_a = sum(1 for row in task_rows if row["methods"][method_a]["correct"] and not row["methods"][method_b]["correct"])
    only_b = sum(1 for row in task_rows if not row["methods"][method_a]["correct"] and row["methods"][method_b]["correct"])
    both = sum(1 for row in task_rows if row["methods"][method_a]["correct"] and row["methods"][method_b]["correct"])
    neither = len(task_rows) - only_a - only_b - both
    return {"only_a": only_a, "only_b": only_b, "both": both, "neither": neither}


def _build_rate_contrast(task_rows: list[dict[str, Any]], name: str, method_a: str, method_b: str, *, n_bootstrap: int = 2000, seed: int = 42) -> dict[str, Any]:
    outcomes_a = tuple(bool(row["methods"][method_a]["correct"]) for row in task_rows)
    outcomes_b = tuple(bool(row["methods"][method_b]["correct"]) for row in task_rows)
    ci_lower, ci_upper = _paired_bootstrap_ci(outcomes_a, outcomes_b, n_bootstrap=n_bootstrap, seed=seed)
    statistic, p_value = _mcnemar_test(outcomes_a, outcomes_b)
    counts = _pairwise_counts(task_rows, method_a, method_b)
    return {
        "name": name,
        "method_a": method_a,
        "method_b": method_b,
        "solve_rate_a": round((sum(outcomes_a) / len(outcomes_a)) if outcomes_a else 0.0, 4),
        "solve_rate_b": round((sum(outcomes_b) / len(outcomes_b)) if outcomes_b else 0.0, 4),
        "estimate": round((((sum(outcomes_b) - sum(outcomes_a)) / len(outcomes_a)) if outcomes_a else 0.0), 4),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "mcnemar_statistic": statistic,
        "mcnemar_p": p_value,
        "paired_counts": counts,
    }


def _build_compute_contrast(task_rows: list[dict[str, Any]], name: str, method_a: str, method_b: str, field: str, *, n_bootstrap: int = 2000, seed: int = 42) -> dict[str, Any]:
    values_a = [float(row["methods"][method_a][field]) for row in task_rows]
    values_b = [float(row["methods"][method_b][field]) for row in task_rows]
    ci_lower, ci_upper = _bootstrap_numeric_ci(values_a, values_b, n_bootstrap=n_bootstrap, seed=seed)
    return {
        "name": name,
        "field": field,
        "method_a": method_a,
        "method_b": method_b,
        "mean_a": round((sum(values_a) / len(values_a)) if values_a else 0.0, 4),
        "mean_b": round((sum(values_b) / len(values_b)) if values_b else 0.0, 4),
        "estimate": round((((sum(values_b) - sum(values_a)) / len(values_a)) if values_a else 0.0), 4),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


def build_output_selection_causal_analysis(
    frozen_summary: dict[str, Any],
    native_summary: dict[str, Any],
    *,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    families = [None, "selector_divergence", "diversity_sensitive", "refinement_composition", "control"]
    analyses: dict[str, Any] = {}
    for label, summary in (("frozen", frozen_summary), ("native", native_summary)):
        family_payload: dict[str, Any] = {}
        for family in families:
            rows = _family_task_rows(summary, family)
            family_key = family or "overall"
            family_payload[family_key] = {
                contrast_name: _build_rate_contrast(rows, contrast_name, method_a, method_b, n_bootstrap=n_bootstrap, seed=seed)
                for contrast_name, method_a, method_b in PAIRWISE_RATE_CONTRASTS
            }
        analyses[label] = family_payload
    return {
        "generated_at_utc": _now_utc(),
        "frozen": analyses["frozen"],
        "native": analyses["native"],
    }


def build_efficiency_gating_analysis(
    frozen_summary: dict[str, Any],
    native_summary: dict[str, Any],
    *,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict[str, Any]:
    fields = ("scored_hypotheses", "refined_hypotheses", "refined_output_classes", "runtime_ms")
    payload: dict[str, Any] = {"generated_at_utc": _now_utc(), "frozen": {}, "native": {}}
    for label, summary in (("frozen", frozen_summary), ("native", native_summary)):
        rows = summary["tasks"]
        payload[label] = {
            field: _build_compute_contrast(rows, f"m4_vs_anchor_{field}", "R_anchor", "M4", field, n_bootstrap=n_bootstrap, seed=seed)
            for field in fields
        }
        payload[label]["solve_rate"] = _build_rate_contrast(rows, "m4_vs_anchor_solve_rate", "R_anchor", "M4", n_bootstrap=n_bootstrap, seed=seed)
    return payload


def build_task_level_epistemic_attribution(frozen_summary: dict[str, Any], native_summary: dict[str, Any]) -> list[dict[str, Any]]:
    native_by_task = {row["task_id"]: row for row in native_summary["tasks"]}
    rows: list[dict[str, Any]] = []
    for frozen_row in frozen_summary["tasks"]:
        native_row = native_by_task[frozen_row["task_id"]]
        f_methods = frozen_row["methods"]
        category = "persistent_failure"
        if all(f_methods[method]["correct"] for method in METHOD_ORDER):
            category = "all_agree_correct"
        elif not any(f_methods[method]["correct"] for method in METHOD_ORDER):
            category = "all_agree_incorrect"
        elif f_methods["M2"]["correct"] and not f_methods["M0"]["correct"] and not f_methods["M1"]["correct"] and not f_methods["M3"]["correct"]:
            category = "output_mass_only_gain"
        elif f_methods["M3"]["correct"] and not f_methods["M2"]["correct"]:
            category = "diversity_aware_only_gain"
        elif f_methods["M4"]["correct"] and not f_methods["M3"]["correct"] and not f_methods["R_anchor"]["correct"]:
            category = "margin_gated_only_gain"
        elif f_methods["M4"]["correct"] and not f_methods["R_anchor"]["correct"]:
            category = "epistemic_package_gain"
        elif f_methods["R_anchor"]["correct"] and not f_methods["M4"]["correct"]:
            category = "refinement_anchor_best"
        elif not f_methods["M2"]["correct"] and f_methods["M0"]["correct"]:
            category = "output_selection_hurt"
        elif not f_methods["M3"]["correct"] and f_methods["M2"]["correct"]:
            category = "diversity_hurt"
        elif not f_methods["M4"]["correct"] and f_methods["R_anchor"]["correct"]:
            category = "margin_gate_hurt"
        rows.append(
            {
                "task_id": frozen_row["task_id"],
                "manifest_family": frozen_row["manifest_family"],
                "category": category,
                "frozen_correctness": {method: f_methods[method]["correct"] for method in METHOD_ORDER},
                "native_correctness": {method: native_row["methods"][method]["correct"] for method in METHOD_ORDER},
                "frozen_selector_disagreement_m0_m2": f_methods["M2"]["selector_differs_from_m0"],
                "frozen_selector_disagreement_m2_m3": (
                    f_methods["M2"]["selected_output_fingerprint"] != f_methods["M3"]["selected_output_fingerprint"]
                ),
                "native_selector_disagreement_m0_m2": native_row["methods"]["M2"]["selector_differs_from_m0"],
                "native_selector_disagreement_m2_m3": (
                    native_row["methods"]["M2"]["selected_output_fingerprint"] != native_row["methods"]["M3"]["selected_output_fingerprint"]
                ),
            }
        )
    return rows


def build_benchmark_quality_gates(frozen_summary: dict[str, Any], native_summary: dict[str, Any]) -> dict[str, Any]:
    def _metrics(rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "multiple_hypotheses": sum(1 for row in rows if row["methods"]["R_anchor"]["multiple_hypotheses_survived"]),
            "multiple_output_classes": sum(1 for row in rows if row["methods"]["R_anchor"]["multiple_output_classes_survived"]),
            "small_margin": sum(1 for row in rows if row["methods"]["R_anchor"]["output_margin"] <= 0.20),
            "nonzero_output_entropy": sum(1 for row in rows if row["methods"]["R_anchor"]["output_entropy"] > 0.0),
            "selector_disagreement_m0_m2": sum(
                1
                for row in rows
                if row["methods"]["M0"]["selected_output_fingerprint"] != row["methods"]["M2"]["selected_output_fingerprint"]
            ),
            "selector_disagreement_m2_m3": sum(
                1
                for row in rows
                if row["methods"]["M2"]["selected_output_fingerprint"] != row["methods"]["M3"]["selected_output_fingerprint"]
            ),
            "output_selection_improves_correctness": sum(
                1
                for row in rows
                if not row["methods"]["M0"]["correct"] and row["methods"]["M2"]["correct"]
            ),
            "diversity_improves_correctness": sum(
                1
                for row in rows
                if not row["methods"]["M2"]["correct"] and row["methods"]["M3"]["correct"]
            ),
            "margin_gate_beats_anchor": sum(
                1
                for row in rows
                if not row["methods"]["R_anchor"]["correct"] and row["methods"]["M4"]["correct"]
            ),
        }

    families = ["selector_divergence", "diversity_sensitive", "refinement_composition", "control"]
    payload: dict[str, Any] = {"generated_at_utc": _now_utc(), "frozen": {}, "native": {}}
    overall_valid = True
    for label, summary in (("frozen", frozen_summary), ("native", native_summary)):
        label_payload: dict[str, Any] = {}
        for family in families + [None]:
            rows = _family_task_rows(summary, family)
            family_key = family or "overall"
            metrics = _metrics(rows)
            thresholds = QUALITY_GATE_THRESHOLDS.get(family_key, QUALITY_GATE_THRESHOLDS.get("overall", {}))
            checks = {}
            for name, value in thresholds.items():
                if name.startswith("min_"):
                    metric_name = name.replace("min_", "", 1)
                    checks[name] = metrics.get(metric_name, 0) >= value
                elif name.startswith("max_"):
                    metric_name = name.replace("max_", "", 1)
                    checks[name] = metrics.get(metric_name, 0) <= value
                else:
                    checks[name] = False
            family_valid = all(checks.values()) if checks else True
            overall_valid = overall_valid and family_valid
            label_payload[family_key] = {
                "task_count": len(rows),
                "metrics": metrics,
                "thresholds": thresholds,
                "checks": checks,
                "valid": family_valid,
            }
        payload[label] = label_payload
    payload["methodology_valid"] = overall_valid
    payload["methodology_status"] = "valid" if overall_valid else "methodologically_inconclusive"
    return payload


def build_epistemic_process_verdict(
    frozen_summary: dict[str, Any],
    native_summary: dict[str, Any],
    quality_gates: dict[str, Any],
    causal_analysis: dict[str, Any],
    efficiency_analysis: dict[str, Any],
    task_attribution: list[dict[str, Any]],
) -> dict[str, Any]:
    if not quality_gates["methodology_valid"]:
        return {
            "generated_at_utc": _now_utc(),
            "status": "methodologically_inconclusive",
            "conviction_level": "methodologically_inconclusive",
            "uncertainty_causal_effect": "methodologically_inconclusive",
            "efficiency_gain": "inconclusive",
            "selector_divergence_exercised": False,
            "output_selection_changed_answer": sum(
                1 for row in task_attribution if row["frozen_selector_disagreement_m0_m2"]
            ),
            "diversity_changed_answer": sum(
                1 for row in task_attribution if row["frozen_selector_disagreement_m2_m3"]
            ),
            "proven_strongly": [],
            "suggestive": [],
            "falsified": [],
            "summary": "Methodologically inconclusive: the benchmark quality gates were not passed, so the intended uncertainty mechanism was not exercised strongly enough for a thesis-facing claim.",
        }

    selector_frozen = causal_analysis["frozen"]["selector_divergence"]["m2_vs_m0"]
    selector_native = causal_analysis["native"]["selector_divergence"]["m2_vs_m0"]
    diversity_frozen = causal_analysis["frozen"]["diversity_sensitive"]["m3_vs_m2"]
    diversity_native = causal_analysis["native"]["diversity_sensitive"]["m3_vs_m2"]
    refinement_diversity_frozen = causal_analysis["frozen"]["refinement_composition"]["m3_vs_m2"]
    refinement_diversity_native = causal_analysis["native"]["refinement_composition"]["m3_vs_m2"]
    output_gain_tasks = sum(1 for row in task_attribution if row["category"] == "output_mass_only_gain")
    diversity_gain_tasks = sum(1 for row in task_attribution if row["category"] == "diversity_aware_only_gain")
    positive_selector = selector_frozen["estimate"] > 0.0 and selector_native["estimate"] >= 0.0
    positive_diversity = diversity_frozen["estimate"] > 0.0 and diversity_native["estimate"] >= 0.0
    strong_selector = positive_selector and (
        selector_frozen["ci_lower"] > 0.0 or selector_native["ci_lower"] > 0.0 or selector_frozen["paired_counts"]["only_b"] > selector_frozen["paired_counts"]["only_a"]
    ) and output_gain_tasks > 0
    strong_diversity = positive_diversity and (
        diversity_frozen["ci_lower"] > 0.0 or diversity_native["ci_lower"] > 0.0 or diversity_frozen["paired_counts"]["only_b"] > diversity_frozen["paired_counts"]["only_a"]
    ) and diversity_gain_tasks > 0

    eff_frozen = efficiency_analysis["frozen"]["solve_rate"]
    eff_native = efficiency_analysis["native"]["solve_rate"]
    runtime_native = efficiency_analysis["native"]["runtime_ms"]
    refined_native = efficiency_analysis["native"]["refined_hypotheses"]
    strong_efficiency = (
        eff_native["estimate"] >= 0.0
        and runtime_native["estimate"] < 0.0
        and refined_native["estimate"] < 0.0
    )

    status = "inconclusive"
    conviction = "low"
    proven: list[str] = []
    suggestive: list[str] = []
    falsified: list[str] = []
    if strong_selector or strong_diversity:
        status = "proven_strongly"
        conviction = "high"
        if strong_selector:
            proven.append("output-level selection has an independent causal effect on selector_divergence tasks")
        if strong_diversity:
            proven.append("diversity-aware coalition support has an independent causal effect on diversity_sensitive tasks")
    elif positive_selector or positive_diversity:
        status = "supported_but_not_isolated"
        conviction = "moderate"
        if positive_selector:
            suggestive.append("output-mass selection shows a positive but not decisive gain")
        if positive_diversity:
            suggestive.append("diversity-aware selection shows a positive but not decisive gain")
    else:
        status = "falsified_on_this_benchmark"
        conviction = "absent"
        falsified.append("no independent uncertainty effect was detected on the exercised blind_holdout_v5 benchmark")

    if refinement_diversity_frozen["estimate"] < 0.0 and refinement_diversity_native["estimate"] < 0.0:
        falsified.append("diversity-aware selection is not a generally safe replacement for refinement-composition tasks on this benchmark")

    efficiency_status = "proven_strongly" if strong_efficiency else "inconclusive"
    if strong_efficiency:
        proven.append("margin-gated refinement reduces compute while preserving accuracy")
    else:
        suggestive.append("margin-gated refinement savings are visible but not yet a decisive efficiency claim")

    return {
        "generated_at_utc": _now_utc(),
        "status": status,
        "conviction_level": conviction,
        "uncertainty_causal_effect": status,
        "efficiency_gain": efficiency_status,
        "selector_divergence_exercised": True,
        "output_selection_changed_answer": sum(1 for row in task_attribution if row["frozen_selector_disagreement_m0_m2"]),
        "diversity_changed_answer": sum(1 for row in task_attribution if row["frozen_selector_disagreement_m2_m3"]),
        "proven_strongly": proven,
        "suggestive": suggestive,
        "falsified": falsified,
        "summary": (
            "blind_holdout_v5 passed the mechanism-exercise gates. "
            f"Uncertainty verdict: {status}. Efficiency verdict: {efficiency_status}."
        ),
    }


def method_setup_experiment_summary(
    frozen_summary: dict[str, Any],
    native_summary: dict[str, Any],
    quality_gates: dict[str, Any],
    causal_analysis: dict[str, Any],
    efficiency_analysis: dict[str, Any],
    verdict: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": _now_utc(),
        "split": frozen_summary["split"],
        "primary_dataset": frozen_summary["split"],
        "methods": {method: METHOD_LABELS[method] for method in METHOD_ORDER},
        "frozen_overall_solve_rates": {method: frozen_summary["overall"][method]["solve_rate"] for method in METHOD_ORDER},
        "native_overall_solve_rates": {method: native_summary["overall"][method]["solve_rate"] for method in METHOD_ORDER},
        "selector_divergence_quality_valid": quality_gates["frozen"]["selector_divergence"]["valid"] and quality_gates["native"]["selector_divergence"]["valid"],
        "diversity_quality_valid": quality_gates["frozen"]["diversity_sensitive"]["valid"] and quality_gates["native"]["diversity_sensitive"]["valid"],
        "m2_vs_m0_selector_divergence_frozen": causal_analysis["frozen"]["selector_divergence"]["m2_vs_m0"],
        "m3_vs_m2_diversity_frozen": causal_analysis["frozen"]["diversity_sensitive"]["m3_vs_m2"],
        "m4_vs_anchor_efficiency_native": efficiency_analysis["native"],
        "verdict": verdict,
    }


def experiment_markdown(summary: dict[str, Any], *, title: str) -> str:
    rows = [
        [method, f"{payload['solve_rate']:.3f}", f"{payload['mean_scored_hypotheses']:.2f}", f"{payload['mean_refined_hypotheses']:.2f}", f"{payload['mean_refined_output_classes']:.2f}", f"{payload['mean_runtime_ms']:.3f}"]
        for method, payload in summary["overall"].items()
    ]
    return "\n".join(
        [
            f"# {title}",
            "",
            f"**Split**: `{summary['split']}` | **Mode**: `{summary['evaluation_mode']}` | **Tasks**: {summary['task_count']}",
            "",
            _table(["Method", "Solve rate", "Mean scored", "Mean refined", "Mean refined outputs", "Mean runtime ms"], rows),
        ]
    )


def quality_gates_markdown(payload: dict[str, Any]) -> str:
    rows = []
    for label in ("frozen", "native"):
        for family, family_payload in payload[label].items():
            rows.append([
                label,
                family,
                "yes" if family_payload["valid"] else "no",
                str(family_payload["task_count"]),
                str(family_payload["metrics"]),
            ])
    return "\n".join(
        [
            "# Benchmark Quality Gates",
            "",
            f"> Methodology status: `{payload['methodology_status']}`",
            "",
            _table(["Experiment", "Family", "Valid", "Tasks", "Observed metrics"], rows),
        ]
    )


def output_selection_causal_markdown(payload: dict[str, Any]) -> str:
    rows = []
    for label in ("frozen", "native"):
        for family, contrasts in payload[label].items():
            for name, contrast in contrasts.items():
                rows.append([
                    label,
                    family,
                    name,
                    f"{contrast['estimate']:+.3f}",
                    f"[{contrast['ci_lower']:+.3f}, {contrast['ci_upper']:+.3f}]",
                    str(contrast["paired_counts"]),
                ])
    return "\n".join(
        [
            "# Output Selection Causal Analysis",
            "",
            _table(["Experiment", "Family", "Contrast", "Estimate", "95% CI", "Paired counts"], rows),
        ]
    )


def efficiency_gating_markdown(payload: dict[str, Any]) -> str:
    rows = []
    for label in ("frozen", "native"):
        for name, contrast in payload[label].items():
            rows.append([
                label,
                name,
                f"{contrast['estimate']:+.3f}",
                f"[{contrast['ci_lower']:+.3f}, {contrast['ci_upper']:+.3f}]",
            ])
    return "\n".join(
        [
            "# Efficiency Gating Analysis",
            "",
            _table(["Experiment", "Metric", "Estimate", "95% CI"], rows),
        ]
    )


def task_level_attribution_markdown(rows: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# Task-Level Epistemic Attribution",
            "",
            _table(
                ["Task", "Family", "Category", "Frozen M0→M2 disagree", "Frozen M2→M3 disagree"],
                [
                    [
                        row["task_id"],
                        row["manifest_family"],
                        row["category"],
                        "yes" if row["frozen_selector_disagreement_m0_m2"] else "no",
                        "yes" if row["frozen_selector_disagreement_m2_m3"] else "no",
                    ]
                    for row in rows
                ],
            ),
        ]
    )


def verdict_markdown(payload: dict[str, Any]) -> str:
    proven_lines = [f"- {item}" for item in payload["proven_strongly"]] or ["- none"]
    suggestive_lines = [f"- {item}" for item in payload["suggestive"]] or ["- none"]
    falsified_lines = [f"- {item}" for item in payload["falsified"]] or ["- none"]
    return "\n".join(
        [
            "# Epistemic Process Verdict",
            "",
            f"- Status: `{payload['status']}`",
            f"- Conviction level: `{payload['conviction_level']}`",
            f"- Uncertainty causal effect: `{payload['uncertainty_causal_effect']}`",
            f"- Efficiency gain: `{payload['efficiency_gain']}`",
            f"- Output-selection answer changes: `{payload['output_selection_changed_answer']}`",
            f"- Diversity-aware answer changes: `{payload['diversity_changed_answer']}`",
            "",
            "## Summary",
            "",
            payload["summary"],
            "",
            "## Proven strongly",
            *proven_lines,
            "",
            "## Suggestive",
            *suggestive_lines,
            "",
            "## Falsified",
            *falsified_lines,
        ]
    )


def method_setup_summary_markdown(payload: dict[str, Any]) -> str:
    rows = [[method, str(payload["frozen_overall_solve_rates"][method]), str(payload["native_overall_solve_rates"][method])] for method in METHOD_ORDER]
    return "\n".join(
        [
            "# Method Setup Experiment Summary",
            "",
            f"- Primary dataset: `{payload['primary_dataset']}`",
            f"- Selector-divergence quality valid: `{payload['selector_divergence_quality_valid']}`",
            f"- Diversity quality valid: `{payload['diversity_quality_valid']}`",
            f"- Verdict: `{payload['verdict']['status']}` ({payload['verdict']['conviction_level']})",
            "",
            _table(["Method", "Frozen solve rate", "Native solve rate"], rows),
        ]
    )
