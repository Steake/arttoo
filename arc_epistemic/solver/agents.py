from __future__ import annotations

from dataclasses import asdict, dataclass

from arc_epistemic.primitives.color import infer_color_mapping
from arc_epistemic.primitives.objects import extract_objects
from arc_epistemic.primitives.patterns import detect_repeat_factor
from arc_epistemic.solver.arbiter import rank_hypotheses
from arc_epistemic.solver.epistemic import derive_epistemic_state
from arc_epistemic.solver.executor import evaluate_hypothesis
from arc_epistemic.solver.hypotheses import Hypothesis, composed_hypothesis, primitive_hypothesis
from arc_epistemic.solver.output_competition import (
    aggregate_output_support,
    select_contested_hypotheses,
    serialize_output_supports,
)
from arc_epistemic.solver.parser import Task
from arc_epistemic.solver.transforms import (
    color_map_transform,
    compose,
    crop_transform,
    largest_object_transform,
    named_transforms,
    tile_transform,
    translate_to_origin_transform,
)

FIRST_PASS_KEEP = 12
SECOND_PASS_KEEP = 6
MAX_GENERATED_HYPOTHESES = 16
MAX_REFINED_HYPOTHESES = 72
MAX_TOTAL_EVALUATIONS = 256


@dataclass(frozen=True)
class SolverConfig:
    name: str
    use_epistemic_scoring: bool
    use_refinement: bool
    use_output_aggregation: bool = False
    use_margin_gated_refinement: bool = False
    first_pass_keep: int = FIRST_PASS_KEEP
    second_pass_keep: int = SECOND_PASS_KEEP
    max_generated_hypotheses: int = MAX_GENERATED_HYPOTHESES
    max_refined_hypotheses: int = MAX_REFINED_HYPOTHESES
    max_total_evaluations: int = MAX_TOTAL_EVALUATIONS
    contested_margin_threshold: float = 0.25
    contested_output_keep: int = 2


@dataclass(frozen=True)
class LoopDiagnostics:
    generated_count: int
    first_pass_scored_count: int
    first_pass_survivor_count: int
    refined_count: int
    second_pass_scored_count: int
    final_survivor_count: int
    evaluation_count: int
    transform_crash_count: int
    shape_mismatch_count: int
    guardrail_ok: bool
    guardrail_messages: tuple[str, ...]
    generated_candidates: tuple[str, ...]
    refined_candidates: tuple[str, ...]
    first_pass_ranking: tuple[dict[str, object], ...]
    final_ranking: tuple[dict[str, object], ...]
    first_pass_pruned: tuple[dict[str, str], ...]
    final_pruned: tuple[dict[str, str], ...]
    agent_disagreements: dict[str, object]
    first_pass_output_competition: tuple[dict[str, object], ...]
    refinement_gate: dict[str, object]


@dataclass(frozen=True)
class PruneRecord:
    description: str
    reason: str


def _hypothesis_snapshot(hypothesis: Hypothesis) -> dict[str, object]:
    return {
        "description": hypothesis.description,
        "family": hypothesis.provenance[0] if hypothesis.provenance else "unknown",
        "complexity": hypothesis.complexity,
        "support_count": hypothesis.support_count,
        "contradiction_count": hypothesis.contradiction_count,
        "unresolved_count": hypothesis.unresolved_count,
        "belief": hypothesis.belief,
        "disbelief": hypothesis.disbelief,
        "uncertainty": hypothesis.uncertainty,
        "score": hypothesis.score,
    }


def _agent_disagreements(hypotheses: list[Hypothesis]) -> dict[str, object]:
    family_counts: dict[str, int] = {}
    for hypothesis in hypotheses[:5]:
        family = hypothesis.provenance[0] if hypothesis.provenance else "unknown"
        family_counts[family] = family_counts.get(family, 0) + 1
    top_scores = [round(hypothesis.score, 6) for hypothesis in hypotheses[:5]]
    unique_families = len(family_counts)
    return {
        "top_family_votes": dict(sorted(family_counts.items())),
        "top_score_band": top_scores,
        "divergent_families": unique_families,
    }


@dataclass(frozen=True)
class LoopResult:
    ranked_hypotheses: list[Hypothesis]
    diagnostics: LoopDiagnostics


PRIMITIVE_BASELINE_CONFIG = SolverConfig(
    name="primitive_baseline_only",
    use_epistemic_scoring=False,
    use_refinement=False,
)
COMPOSITION_BASELINE_CONFIG = SolverConfig(
    name="primitive_plus_bounded_compositions",
    use_epistemic_scoring=False,
    use_refinement=True,
)
EPISTEMIC_NO_REFINEMENT_CONFIG = SolverConfig(
    name="epistemic_no_refinement",
    use_epistemic_scoring=True,
    use_refinement=False,
)
FULL_COAGENCY_CONFIG = SolverConfig(
    name="full_epistemic_coagency",
    use_epistemic_scoring=True,
    use_refinement=True,
)


def _background_for_task(task: Task) -> int:
    colors = [example.input.majority_color() for example in task.train]
    colors.sort()
    return colors[0]


def solver_variants() -> tuple[SolverConfig, ...]:
    return (
        PRIMITIVE_BASELINE_CONFIG,
        COMPOSITION_BASELINE_CONFIG,
        EPISTEMIC_NO_REFINEMENT_CONFIG,
        FULL_COAGENCY_CONFIG,
    )


def generate_hypotheses(task: Task, config: SolverConfig | None = None) -> list[Hypothesis]:
    background = _background_for_task(task)
    hypotheses: list[Hypothesis] = []
    for description, transform, complexity, allows_shape_change in named_transforms():
        hypotheses.append(
            primitive_hypothesis(
                description=description,
                transform=transform,
                family="symmetry",
                complexity=complexity,
                allows_shape_change=allows_shape_change,
            )
        )
    hypotheses.append(
        primitive_hypothesis(
            description="crop_to_content",
            transform=crop_transform(background=background),
            family="geometry",
            complexity=1,
            allows_shape_change=True,
        )
    )
    hypotheses.append(
        primitive_hypothesis(
            description="translate_to_origin",
            transform=translate_to_origin_transform(background=background),
            family="geometry",
            complexity=1,
            allows_shape_change=False,
        )
    )
    hypotheses.append(
        primitive_hypothesis(
            description="largest_object",
            transform=largest_object_transform(lambda grid: extract_objects(grid, background=background)),
            family="objects",
            complexity=1,
            allows_shape_change=True,
        )
    )
    color_mapping = infer_color_mapping(
        [example.input for example in task.train],
        [example.output for example in task.train],
    )
    if color_mapping is not None:
        hypotheses.append(
            primitive_hypothesis(
                description=f"color_map_{sorted(color_mapping.items())}",
                transform=color_map_transform(color_mapping),
                family="color",
                complexity=max(2, len(color_mapping)),
                allows_shape_change=False,
            )
        )
    repeat_factor: tuple[int, int] | None = None
    for example in task.train:
        factor = detect_repeat_factor(example.input, example.output)
        if factor is None:
            repeat_factor = None
            break
        if repeat_factor is None:
            repeat_factor = factor
        elif repeat_factor != factor:
            repeat_factor = None
            break
    if repeat_factor is not None:
        hypotheses.append(
            primitive_hypothesis(
                description=f"tile_{repeat_factor[0]}x{repeat_factor[1]}",
                transform=tile_transform(*repeat_factor),
                family="patterns",
                complexity=1,
                allows_shape_change=True,
            )
        )
    ordered = hypotheses[: (config.max_generated_hypotheses if config else MAX_GENERATED_HYPOTHESES)]
    return ordered


def _baseline_score(total_pairs: int, support_count: int, contradiction_count: int, partial_credit: float) -> tuple[float, float, float, float]:
    if total_pairs <= 0:
        return (0.0, 0.0, 1.0, -1.0)
    belief = support_count / total_pairs
    disbelief = contradiction_count / total_pairs
    uncertainty = max(0.0, 1.0 - belief - disbelief)
    score = belief + 0.05 * partial_credit - disbelief
    return (belief, disbelief, uncertainty, score)


def score_hypotheses(task: Task, hypotheses: list[Hypothesis], config: SolverConfig) -> tuple[list[Hypothesis], int, int]:
    scored: list[Hypothesis] = []
    total_pairs = len(task.train)
    transform_crash_count = 0
    shape_mismatch_count = 0
    for hypothesis in hypotheses:
        result = evaluate_hypothesis(hypothesis, task.train)
        if config.use_epistemic_scoring:
            belief, disbelief, uncertainty, score = derive_epistemic_state(
                total_pairs=total_pairs,
                support_count=result.support_count,
                contradiction_count=result.contradiction_count,
                unresolved_count=result.unresolved_count,
                partial_credit=result.partial_credit,
            )
        else:
            belief, disbelief, uncertainty, score = _baseline_score(
                total_pairs=total_pairs,
                support_count=result.support_count,
                contradiction_count=result.contradiction_count,
                partial_credit=result.partial_credit,
            )
        transform_crash_count += result.exception_count
        shape_mismatch_count += result.shape_mismatch_count
        scored.append(
            hypothesis.with_epistemics(
                support_count=result.support_count,
                contradiction_count=result.contradiction_count,
                unresolved_count=result.unresolved_count,
                belief=belief,
                disbelief=disbelief,
                uncertainty=uncertainty,
                partial_credit=result.partial_credit,
                score=score,
            )
        )
    return (rank_hypotheses(scored), transform_crash_count, shape_mismatch_count)


def critic_prune(hypotheses: list[Hypothesis], keep: int, config: SolverConfig) -> tuple[list[Hypothesis], tuple[PruneRecord, ...]]:
    survivors: list[Hypothesis] = []
    pruned: list[PruneRecord] = []
    guaranteed_keep = min(3, keep)
    for hypothesis in hypotheses[:guaranteed_keep]:
        survivors.append(hypothesis)
    capped_index = len(hypotheses)
    for index, hypothesis in enumerate(hypotheses[guaranteed_keep:], start=guaranteed_keep):
        if config.use_epistemic_scoring:
            should_drop = hypothesis.contradiction_count > max(1, hypothesis.support_count + hypothesis.unresolved_count)
            reason = "contradiction_dominated"
        else:
            should_drop = hypothesis.contradiction_count > max(1, hypothesis.support_count)
            reason = "baseline_contradiction_dominated"
        if should_drop:
            pruned.append(PruneRecord(description=hypothesis.description, reason=reason))
            continue
        survivors.append(hypothesis)
        if len(survivors) >= keep:
            capped_index = index + 1
            break
    for hypothesis in hypotheses[capped_index:]:
        pruned.append(PruneRecord(description=hypothesis.description, reason="keep_cap_reached"))
    return (survivors, tuple(pruned))


def refine_hypotheses(task: Task, survivors: list[Hypothesis], config: SolverConfig) -> list[Hypothesis]:
    refinements: list[Hypothesis] = []
    for survivor in survivors[: config.second_pass_keep]:
        for description, transform, _, allows_shape_change in named_transforms()[1:]:
            composed = composed_hypothesis(
                description=f"{survivor.description} -> {description}",
                transform=compose(survivor.transform, transform),
                left=survivor,
                right_family="symmetry",
                allows_shape_change=allows_shape_change,
            )
            refinements.append(composed)
        refinements.append(
            composed_hypothesis(
                description=f"{survivor.description} -> crop_to_content",
                transform=compose(survivor.transform, crop_transform(background=_background_for_task(task))),
                left=survivor,
                right_family="geometry",
                allows_shape_change=True,
            )
        )
    return refinements[: config.max_refined_hypotheses]


def run_coagency_loop(task: Task, config: SolverConfig = FULL_COAGENCY_CONFIG) -> LoopResult:
    guardrail_messages: list[str] = []
    train_count = len(task.train)

    generated = generate_hypotheses(task, config=config)
    if len(generated) > config.max_generated_hypotheses:
        generated = generated[: config.max_generated_hypotheses]
        guardrail_messages.append("generated hypothesis cap enforced")

    first_pass, first_crashes, first_shape_mismatches = score_hypotheses(task, generated, config=config)
    survivors, first_pruned = critic_prune(first_pass, keep=config.first_pass_keep, config=config)
    first_pass_output_competition: tuple[dict[str, object], ...] = tuple()
    refinement_gate: dict[str, object] = {
        "mode": "broad_refinement",
        "contested": False,
        "selected_outputs": 0,
        "selected_hypotheses": len(survivors),
    }
    refine_source = survivors
    if task.test:
        first_pass_supports = serialize_output_supports(
            aggregate_output_support(survivors, task.test[0].input) if survivors else tuple()
        )
        first_pass_output_competition = first_pass_supports
        if config.use_margin_gated_refinement and survivors:
            refine_source, refinement_gate = select_contested_hypotheses(
                survivors,
                task.test[0].input,
                margin_threshold=config.contested_margin_threshold,
                keep_outputs=config.contested_output_keep,
            )

    refined: list[Hypothesis] = []
    if config.use_refinement:
        # Enforce evaluation budget before expanding refined candidates.
        first_pass_evals = len(generated) * train_count
        remaining_budget = config.max_total_evaluations - first_pass_evals
        max_refined_by_budget = max(0, remaining_budget // max(train_count, 1)) - len(survivors)
        budget_cap = min(config.max_refined_hypotheses, max(0, max_refined_by_budget))
        refined = refine_hypotheses(task, refine_source, config=config)
        if len(refined) > budget_cap:
            refined = refined[:budget_cap]
            guardrail_messages.append("refined hypothesis cap enforced")

    second_input = survivors + refined if config.use_refinement else survivors
    second_pass, second_crashes, second_shape_mismatches = score_hypotheses(task, second_input, config=config)
    final_survivors, final_pruned = critic_prune(second_pass, keep=config.first_pass_keep, config=config)
    evaluation_count = (len(generated) + len(second_input)) * train_count
    if evaluation_count > config.max_total_evaluations:
        guardrail_messages.append("evaluation count cap exceeded")
    diagnostics = LoopDiagnostics(
        generated_count=len(generated),
        first_pass_scored_count=len(first_pass),
        first_pass_survivor_count=len(survivors),
        refined_count=len(refined),
        second_pass_scored_count=len(second_pass),
        final_survivor_count=len(final_survivors),
        evaluation_count=evaluation_count,
        transform_crash_count=first_crashes + second_crashes,
        shape_mismatch_count=first_shape_mismatches + second_shape_mismatches,
        guardrail_ok=not guardrail_messages,
        guardrail_messages=tuple(guardrail_messages),
        generated_candidates=tuple(hypothesis.description for hypothesis in generated),
        refined_candidates=tuple(hypothesis.description for hypothesis in refined),
        first_pass_ranking=tuple(_hypothesis_snapshot(hypothesis) for hypothesis in first_pass),
        final_ranking=tuple(_hypothesis_snapshot(hypothesis) for hypothesis in second_pass),
        first_pass_pruned=tuple(asdict(record) for record in first_pruned),
        final_pruned=tuple(asdict(record) for record in final_pruned),
        agent_disagreements=_agent_disagreements(first_pass),
        first_pass_output_competition=first_pass_output_competition,
        refinement_gate=refinement_gate,
    )
    return LoopResult(ranked_hypotheses=final_survivors, diagnostics=diagnostics)
