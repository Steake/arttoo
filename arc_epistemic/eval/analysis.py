from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from arc_epistemic.eval.fixtures import FixtureTask
from arc_epistemic.solver.agents import (
    COMPOSITION_BASELINE_CONFIG,
    EPISTEMIC_NO_REFINEMENT_CONFIG,
    FULL_COAGENCY_CONFIG,
    PRIMITIVE_BASELINE_CONFIG,
    SolverConfig,
)
from arc_epistemic.solver.solver import SolveResult, solve_task_with_diagnostics
from arc_epistemic.utils.grid import Grid
from arc_epistemic.primitives.objects import extract_objects


@dataclass(frozen=True)
class FailureTyping:
    primary_class: str | None
    tags: tuple[str, ...]
    suspected_root_cause: str | None


@dataclass(frozen=True)
class CaseDiagnostic:
    task_id: str
    split: str
    variant: str
    runtime_ms: float
    success_attempt_1: bool
    success_attempt_2: bool
    expected_output: list[list[int]]
    attempt_1: list[list[int]]
    attempt_2: list[list[int]]
    winning_hypothesis: str
    second_hypothesis: str
    winning_belief: float
    winning_disbelief: float
    winning_uncertainty: float
    winning_score: float
    generated_count: int
    first_pass_survivor_count: int
    refined_count: int
    evaluation_count: int
    transform_crash_count: int
    shape_mismatch_count: int
    guardrail_ok: bool
    guardrail_messages: tuple[str, ...]
    failure_primary_class: str | None
    failure_tags: tuple[str, ...]
    winning_family: str
    telemetry: dict[str, Any]


@dataclass(frozen=True)
class AggregateMetrics:
    split: str
    variant: str
    task_count: int
    test_case_count: int
    attempt_1_exact_rate: float
    attempt_1_or_2_exact_rate: float
    attempt_2_rescue_count: int
    average_runtime_ms: float
    max_runtime_ms: float
    average_generated_count: float
    average_first_pass_survivor_count: float
    average_refined_count: float
    average_belief: float
    average_disbelief: float
    average_uncertainty: float
    average_winning_score: float
    shape_mismatch_failure_count: int
    transform_crash_count: int
    contradiction_dominated_failure_count: int
    unresolved_high_uncertainty_failure_count: int
    no_viable_hypothesis_count: int
    family_win_counts: dict[str, int]
    failure_primary_class_counts: dict[str, int]
    failure_tag_counts: dict[str, int]
    generated_at_utc: str


def variant_configs() -> tuple[SolverConfig, ...]:
    return (
        PRIMITIVE_BASELINE_CONFIG,
        COMPOSITION_BASELINE_CONFIG,
        EPISTEMIC_NO_REFINEMENT_CONFIG,
        FULL_COAGENCY_CONFIG,
    )


def _grid_equals(left: Grid, right: Grid) -> bool:
    return left.cache_key() == right.cache_key()


def _object_count(grid: Grid) -> int:
    return len(extract_objects(grid, background=grid.majority_color()))


def _failure_root_cause(primary_class: str | None) -> str | None:
    causes = {
        "unsupported_pattern": "fixture encodes a pattern family not currently covered by available primitives",
        "wrong_shape": "selected transform family changed dimensions incorrectly",
        "object_count_mismatch": "solver failed to preserve or infer the expected number of objects",
        "symmetry_failure": "symmetry family or composition ranked incorrectly for the task geometry",
        "colour_mapping_failure": "selected hypothesis preserved colors or inferred color mapping incorrectly",
        "size_inference_failure": "output size or repetition factor inference failed",
        "composition_failure": "primitive families existed but bounded composition did not recover the target program",
        "ranking_error": "a correct or stronger lower-ranked hypothesis lost the final tie-break",
        "no_candidate_solution": "all candidate programs were pruned or failed to produce viable outputs",
    }
    return causes.get(primary_class)


def categorize_failure(fixture: FixtureTask, result: SolveResult) -> FailureTyping:
    if not result.ranked_hypotheses:
        return FailureTyping("no_candidate_solution", fixture.failure_tags, _failure_root_cause("no_candidate_solution"))
    expected = fixture.expected_outputs[0]
    predicted = result.predictions[0][0]
    if _grid_equals(predicted, expected):
        return FailureTyping(None, tuple(), None)

    tags = set(fixture.failure_tags)
    if not fixture.expect_exact:
        tags.add("known_regression_fixture")
    top = result.ranked_hypotheses[0]
    selected = result.selected_hypotheses[0] if result.selected_hypotheses else ""
    if len(result.predictions[0]) >= 2 and _grid_equals(result.predictions[0][1], expected):
        tags.add("attempt_2_rescue_available")
        return FailureTyping("ranking_error", tuple(sorted(tags)), _failure_root_cause("ranking_error"))
    if not fixture.expect_exact:
        tags.add("unsupported_pattern")
    if predicted.shape != expected.shape:
        if "unsupported_pattern" in tags:
            primary = "unsupported_pattern"
        elif _object_count(predicted) != _object_count(expected):
            primary = "object_count_mismatch"
        elif selected.startswith("tile_") or "tile_" in selected:
            primary = "size_inference_failure"
        elif " -> " in selected:
            primary = "composition_failure"
        else:
            primary = "wrong_shape"
        return FailureTyping(primary, tuple(sorted(tags)), _failure_root_cause(primary))
    if set(predicted.unique_colors()) != set(expected.unique_colors()):
        primary = "colour_mapping_failure"
        return FailureTyping(primary, tuple(sorted(tags)), _failure_root_cause(primary))
    if _object_count(predicted) != _object_count(expected):
        primary = "object_count_mismatch"
        return FailureTyping(primary, tuple(sorted(tags)), _failure_root_cause(primary))
    if any(keyword in selected for keyword in ("rotate", "flip")):
        primary = "symmetry_failure"
        return FailureTyping(primary, tuple(sorted(tags)), _failure_root_cause(primary))
    if " -> " in selected:
        primary = "composition_failure"
        return FailureTyping(primary, tuple(sorted(tags)), _failure_root_cause(primary))
    if top.uncertainty >= 0.5:
        tags.add("high_uncertainty")
        return FailureTyping("no_candidate_solution", tuple(sorted(tags)), _failure_root_cause("no_candidate_solution"))
    return FailureTyping("ranking_error", tuple(sorted(tags)), _failure_root_cause("ranking_error"))


def _telemetry(result: SolveResult, expected: Grid, runtime_ms: float = 0.0) -> dict[str, Any]:
    winning = result.ranked_hypotheses[0] if result.ranked_hypotheses else None
    second = result.ranked_hypotheses[1] if len(result.ranked_hypotheses) > 1 else None
    disagreements = result.loop_diagnostics.agent_disagreements
    return {
        "deterministic_fingerprint": result.run_fingerprint,
        "expected_fingerprint": expected.fingerprint(),
        # Runtime is measured outside the solver loop to include serialisation overhead
        "runtime_ms": round(runtime_ms, 4),
        "generated_candidates": list(result.loop_diagnostics.generated_candidates),
        "refined_candidates": list(result.loop_diagnostics.refined_candidates),
        # first_pass_ranking: hypothesis snapshots after first evaluation pass (before refinement)
        "first_pass_ranking": list(result.loop_diagnostics.first_pass_ranking),
        # final_ranking: hypothesis snapshots after second evaluation pass (after refinement)
        "final_ranking": list(result.loop_diagnostics.final_ranking),
        # pruning: reasons why hypotheses were dropped at each pass
        "first_pass_pruned": list(result.loop_diagnostics.first_pass_pruned),
        "final_pruned": list(result.loop_diagnostics.final_pruned),
        # agent_disagreements: divergence among top-5 hypothesis families
        "agent_disagreements": disagreements,
        # selection: which hypotheses were chosen as attempt_1 and attempt_2
        "selection": {
            "attempt_1_hypothesis": winning.description if winning else "",
            "attempt_2_hypothesis": second.description if second else "",
            "selected_hypotheses": list(result.selected_hypotheses),
            "selection_telemetry": result.selection_telemetry,
        },
        # confidence: epistemic values for the winning hypothesis
        "confidence": {
            "belief": winning.belief if winning else 0.0,
            "disbelief": winning.disbelief if winning else 0.0,
            "uncertainty": winning.uncertainty if winning else 1.0,
            "score": winning.score if winning else -1.0,
        },
        "output_confidence": {
            "selection_mode": result.selection_telemetry.get("mode", "single_best_hypothesis"),
            "output_uncertainty": result.selection_telemetry.get("output_uncertainty", 1.0),
            "output_entropy": result.selection_telemetry.get("output_entropy", 1.0),
            "output_margin": result.selection_telemetry.get("output_margin", 0.0),
            "winner_changed_vs_single_best": result.selection_telemetry.get("winner_changed_vs_single_best", False),
            "output_supports": result.selection_telemetry.get("output_supports", []),
        },
        # step_counts: search breadth and depth statistics
        "step_counts": {
            "generated_count": result.loop_diagnostics.generated_count,
            "first_pass_scored_count": result.loop_diagnostics.first_pass_scored_count,
            "first_pass_survivor_count": result.loop_diagnostics.first_pass_survivor_count,
            "refined_count": result.loop_diagnostics.refined_count,
            "second_pass_scored_count": result.loop_diagnostics.second_pass_scored_count,
            "final_survivor_count": result.loop_diagnostics.final_survivor_count,
            "evaluation_count": result.loop_diagnostics.evaluation_count,
        },
        "first_pass_output_competition": list(result.loop_diagnostics.first_pass_output_competition),
        "refinement_gate": result.loop_diagnostics.refinement_gate,
    }


def _case_diagnostic(fixture: FixtureTask, config: SolverConfig, split: str) -> tuple[CaseDiagnostic, SolveResult]:
    started = time.perf_counter()
    result = solve_task_with_diagnostics(fixture.task, config=config)
    runtime_ms = (time.perf_counter() - started) * 1000.0
    expected = fixture.expected_outputs[0]
    attempt_1, attempt_2 = result.predictions[0]
    success_attempt_1 = _grid_equals(attempt_1, expected)
    success_attempt_2 = success_attempt_1 or _grid_equals(attempt_2, expected)
    failure = FailureTyping(None, tuple(), None) if success_attempt_2 else categorize_failure(fixture, result)
    winning = result.ranked_hypotheses[0] if result.ranked_hypotheses else None
    second = result.ranked_hypotheses[1] if len(result.ranked_hypotheses) > 1 else None
    diagnostic = CaseDiagnostic(
        task_id=fixture.task_id,
        split=split,
        variant=config.name,
        runtime_ms=runtime_ms,
        success_attempt_1=success_attempt_1,
        success_attempt_2=success_attempt_2,
        expected_output=expected.to_list(),
        attempt_1=attempt_1.to_list(),
        attempt_2=attempt_2.to_list(),
        winning_hypothesis=winning.description if winning else "",
        second_hypothesis=second.description if second else "",
        winning_belief=winning.belief if winning else 0.0,
        winning_disbelief=winning.disbelief if winning else 0.0,
        winning_uncertainty=winning.uncertainty if winning else 1.0,
        winning_score=winning.score if winning else -1.0,
        generated_count=result.loop_diagnostics.generated_count,
        first_pass_survivor_count=result.loop_diagnostics.first_pass_survivor_count,
        refined_count=result.loop_diagnostics.refined_count,
        evaluation_count=result.loop_diagnostics.evaluation_count,
        transform_crash_count=result.loop_diagnostics.transform_crash_count,
        shape_mismatch_count=result.loop_diagnostics.shape_mismatch_count,
        guardrail_ok=result.loop_diagnostics.guardrail_ok,
        guardrail_messages=result.loop_diagnostics.guardrail_messages,
        failure_primary_class=failure.primary_class,
        failure_tags=failure.tags,
        winning_family=winning.provenance[0] if winning and winning.provenance else "none",
        telemetry=_telemetry(result, expected, runtime_ms=runtime_ms),
    )
    return (diagnostic, result)


def evaluate_fixture_batch(fixtures: list[FixtureTask], config: SolverConfig, split: str = "all") -> dict[str, object]:
    case_diagnostics: list[CaseDiagnostic] = []
    ranking_prefix_mismatches: list[str] = []
    for fixture in fixtures:
        case_diagnostic, result = _case_diagnostic(fixture, config, split=split)
        case_diagnostics.append(case_diagnostic)
        if fixture.ranking_prefix:
            observed = tuple(h.description for h in result.ranked_hypotheses[: len(fixture.ranking_prefix)])
            if observed != fixture.ranking_prefix:
                ranking_prefix_mismatches.append(fixture.task_id)

    task_count = len(fixtures)
    test_case_count = len(case_diagnostics)
    attempt_1_hits = sum(1 for case in case_diagnostics if case.success_attempt_1)
    attempt_2_hits = sum(1 for case in case_diagnostics if case.success_attempt_2)
    runtimes = [case.runtime_ms for case in case_diagnostics]
    family_counts = Counter(case.winning_family for case in case_diagnostics if case.winning_family)
    failure_primary_counts = Counter(case.failure_primary_class for case in case_diagnostics if case.failure_primary_class)
    failure_tag_counts = Counter(tag for case in case_diagnostics for tag in case.failure_tags)
    contradiction_failures = sum(1 for case in case_diagnostics if case.failure_primary_class == "ranking_error" and case.winning_disbelief >= 0.5)
    uncertainty_failures = sum(1 for case in case_diagnostics if "high_uncertainty" in case.failure_tags)
    no_viable_count = sum(1 for case in case_diagnostics if case.failure_primary_class == "no_candidate_solution")
    aggregate = AggregateMetrics(
        split=split,
        variant=config.name,
        task_count=task_count,
        test_case_count=test_case_count,
        attempt_1_exact_rate=(attempt_1_hits / test_case_count) if test_case_count else 0.0,
        attempt_1_or_2_exact_rate=(attempt_2_hits / test_case_count) if test_case_count else 0.0,
        attempt_2_rescue_count=attempt_2_hits - attempt_1_hits,
        average_runtime_ms=(sum(runtimes) / len(runtimes)) if runtimes else 0.0,
        max_runtime_ms=max(runtimes) if runtimes else 0.0,
        average_generated_count=sum(case.generated_count for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_first_pass_survivor_count=sum(case.first_pass_survivor_count for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_refined_count=sum(case.refined_count for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_belief=sum(case.winning_belief for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_disbelief=sum(case.winning_disbelief for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_uncertainty=sum(case.winning_uncertainty for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        average_winning_score=sum(case.winning_score for case in case_diagnostics) / test_case_count if test_case_count else 0.0,
        shape_mismatch_failure_count=sum(case.shape_mismatch_count for case in case_diagnostics),
        transform_crash_count=sum(case.transform_crash_count for case in case_diagnostics),
        contradiction_dominated_failure_count=contradiction_failures,
        unresolved_high_uncertainty_failure_count=uncertainty_failures,
        no_viable_hypothesis_count=no_viable_count,
        family_win_counts=dict(sorted(family_counts.items())),
        failure_primary_class_counts=dict(sorted(failure_primary_counts.items())),
        failure_tag_counts=dict(sorted(failure_tag_counts.items())),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "split": split,
        "aggregate": asdict(aggregate),
        "per_task": [asdict(case) for case in case_diagnostics],
        "ranking_prefix_mismatches": ranking_prefix_mismatches,
    }


def compare_variants(fixtures: list[FixtureTask], split: str = "all") -> dict[str, object]:
    results: dict[str, dict[str, object]] = {}
    baseline = evaluate_fixture_batch(fixtures, PRIMITIVE_BASELINE_CONFIG, split=split)
    results[PRIMITIVE_BASELINE_CONFIG.name] = baseline
    baseline_score = baseline["aggregate"]["attempt_1_or_2_exact_rate"]
    baseline_runtime = baseline["aggregate"]["average_runtime_ms"]
    baseline_winning_score = baseline["aggregate"]["average_winning_score"]
    deltas: dict[str, dict[str, float]] = {}
    for config in variant_configs()[1:]:
        batch = evaluate_fixture_batch(fixtures, config, split=split)
        results[config.name] = batch
        deltas[config.name] = {
            "solve_rate_delta_vs_baseline": batch["aggregate"]["attempt_1_or_2_exact_rate"] - baseline_score,
            "runtime_delta_ms_vs_baseline": batch["aggregate"]["average_runtime_ms"] - baseline_runtime,
            "winning_score_delta_vs_baseline": batch["aggregate"]["average_winning_score"] - baseline_winning_score,
        }
    return {"split": split, "baseline": PRIMITIVE_BASELINE_CONFIG.name, "variants": results, "deltas": deltas}


def group_failures(per_task: list[dict[str, object]], split: str = "all") -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    tag_counts: Counter[str] = Counter()
    # Separate counters for distinct failure categories (C: failure metric hygiene)
    final_task_failures: list[str] = []
    candidate_transform_failures_total = 0
    shape_mismatch_rejections_total = 0
    unsupported_pattern_exits: list[str] = []
    for item in per_task:
        primary = item.get("failure_primary_class")
        if primary:
            grouped[str(primary)].append(item)
            final_task_failures.append(str(item["task_id"]))
        if str(primary) == "unsupported_pattern":
            unsupported_pattern_exits.append(str(item["task_id"]))
        for tag in item.get("failure_tags", []):
            tag_counts[str(tag)] += 1
        candidate_transform_failures_total += int(item.get("transform_crash_count", 0))
        shape_mismatch_rejections_total += int(item.get("shape_mismatch_count", 0))
    summary = {
        category: {
            "split": split,
            "count": len(items),
            "task_ids": sorted(item["task_id"] for item in items),
            "representatives": [item["task_id"] for item in items[:3]],
            "failure_tags": dict(sorted(Counter(tag for item in items for tag in item.get("failure_tags", [])).items())),
            "suspected_root_cause": _failure_root_cause(category),
        }
        for category, items in sorted(grouped.items())
    }
    return {
        "split": split,
        "failure_classes": summary,
        "global_tag_counts": dict(sorted(tag_counts.items())),
        # Separate hygiene counters (not collapsed into one ambiguous failure_count)
        "final_task_failure_count": len(final_task_failures),
        "final_task_failure_ids": sorted(final_task_failures),
        "candidate_transform_failure_count": candidate_transform_failures_total,
        "shape_mismatch_rejection_count": shape_mismatch_rejections_total,
        "unsupported_pattern_exit_count": len(unsupported_pattern_exits),
        "unsupported_pattern_exit_ids": sorted(unsupported_pattern_exits),
    }


def build_scorecard(
    benchmark: dict[str, object],
    ablation: dict[str, object],
    determinism: dict[str, object],
    failures: dict[str, object],
) -> dict[str, object]:
    aggregate = benchmark["aggregate"]
    baseline_name = ablation["baseline"]
    baseline_rate = ablation["variants"][baseline_name]["aggregate"]["attempt_1_or_2_exact_rate"]
    full_rate = aggregate["attempt_1_or_2_exact_rate"]
    return {
        "task_split": benchmark["split"],
        "exact_solve_rate": full_rate,
        "primitive_baseline_solve_rate": baseline_rate,
        "lift": full_rate - baseline_rate,
        "determinism_pass": bool(
            determinism["stable_outputs"] and determinism["stable_rankings"] and determinism["stable_metrics"]
        ),
        # Separated failure categories (C: failure metric hygiene)
        "failure_counts_by_class": aggregate["failure_primary_class_counts"],
        "final_task_failure_count": failures.get("final_task_failure_count", 0),
        "candidate_transform_failure_count": failures.get("candidate_transform_failure_count", 0),
        "shape_mismatch_rejection_count": failures.get("shape_mismatch_rejection_count", 0),
        "unsupported_pattern_exit_count": failures.get("unsupported_pattern_exit_count", 0),
        # Epistemic calibration summary (B: uncertainty audit)
        "average_winning_uncertainty": aggregate["average_uncertainty"],
        "average_winning_belief": aggregate["average_belief"],
        "average_runtime_ms": aggregate["average_runtime_ms"],
        "worst_case_runtime_ms": aggregate["max_runtime_ms"],
        "evaluated_tasks": aggregate["task_count"],
        "timestamp_utc": aggregate["generated_at_utc"],
    }


def serialize_json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
