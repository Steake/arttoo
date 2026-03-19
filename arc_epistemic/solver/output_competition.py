from __future__ import annotations

from dataclasses import dataclass

from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.hypotheses import Hypothesis
from arc_epistemic.utils.grid import Grid


@dataclass(frozen=True)
class OutputSupport:
    key: tuple[tuple[int, int], bytes]
    output: Grid
    hypotheses: tuple[Hypothesis, ...]
    total_mass: float
    normalized_mass: float
    margin_to_runner_up: float
    best_hypothesis: Hypothesis


def evidence_mass(hypothesis: Hypothesis) -> float:
    """Deterministic non-negative support for output-level aggregation."""
    return max(0.0, hypothesis.belief + 0.5 * hypothesis.partial_credit - hypothesis.disbelief)


def aggregate_output_support(
    hypotheses: list[Hypothesis],
    test_input: Grid,
) -> tuple[OutputSupport, ...]:
    grouped: dict[tuple[tuple[int, int], bytes], dict[str, object]] = {}
    total_mass = 0.0
    for hypothesis in hypotheses:
        predicted = apply_hypothesis(hypothesis, test_input)
        if predicted is None:
            continue
        key = predicted.cache_key()
        bucket = grouped.setdefault(
            key,
            {
                "output": predicted,
                "hypotheses": [],
                "total_mass": 0.0,
                "best_hypothesis": hypothesis,
            },
        )
        bucket["hypotheses"].append(hypothesis)
        bucket["total_mass"] += evidence_mass(hypothesis)
        total_mass += evidence_mass(hypothesis)

    ranked = sorted(
        grouped.items(),
        key=lambda item: (
            -float(item[1]["total_mass"]),
            -float(item[1]["best_hypothesis"].score),
            item[1]["best_hypothesis"].contradiction_count,
            item[1]["best_hypothesis"].complexity,
            item[1]["best_hypothesis"].description,
        ),
    )
    supports: list[OutputSupport] = []
    for index, (key, payload) in enumerate(ranked):
        runner_up_mass = float(ranked[index + 1][1]["total_mass"]) if index + 1 < len(ranked) else 0.0
        mass = float(payload["total_mass"])
        normalized = (mass / total_mass) if total_mass > 0.0 else 0.0
        margin = mass - runner_up_mass
        supports.append(
            OutputSupport(
                key=key,
                output=payload["output"],
                hypotheses=tuple(payload["hypotheses"]),
                total_mass=mass,
                normalized_mass=normalized,
                margin_to_runner_up=margin,
                best_hypothesis=payload["best_hypothesis"],
            )
        )
    return tuple(supports)


def output_uncertainty(supports: tuple[OutputSupport, ...]) -> float:
    if not supports:
        return 1.0
    if len(supports) == 1:
        return 0.0
    top = supports[0].total_mass
    runner_up = supports[1].total_mass
    if top <= 0.0:
        return 1.0
    return max(0.0, min(1.0, runner_up / top))


def select_top_two_output_classes(
    hypotheses: list[Hypothesis],
    test_input: Grid,
) -> tuple[Hypothesis | None, Hypothesis | None, tuple[OutputSupport, ...]]:
    supports = aggregate_output_support(hypotheses, test_input)
    if not supports:
        return (None, None, tuple())
    first = supports[0].best_hypothesis
    second = supports[1].best_hypothesis if len(supports) > 1 else None
    return (first, second, supports)


def select_contested_hypotheses(
    hypotheses: list[Hypothesis],
    test_input: Grid,
    *,
    margin_threshold: float,
    keep_outputs: int,
) -> tuple[list[Hypothesis], dict[str, object]]:
    supports = aggregate_output_support(hypotheses, test_input)
    if not supports:
        return (
            hypotheses,
            {
                "mode": "no_outputs",
                "contested": False,
                "output_uncertainty": 1.0,
                "selected_outputs": 0,
                "selected_hypotheses": len(hypotheses),
            },
        )
    uncertainty = output_uncertainty(supports)
    contested = len(supports) > 1 and uncertainty >= margin_threshold
    if not contested:
        top_key = supports[0].key
        selected = []
        for hypothesis in hypotheses:
            predicted = apply_hypothesis(hypothesis, test_input)
            if predicted is None:
                continue
            if predicted.cache_key() == top_key:
                selected.append(hypothesis)
        return (
            selected,
            {
                "mode": "not_contested",
                "contested": False,
                "output_uncertainty": round(uncertainty, 6),
                "selected_outputs": 1,
                "selected_hypotheses": len(selected),
                "top_output_mass": round(supports[0].total_mass, 6),
            },
        )
    allowed = {support.key for support in supports[:keep_outputs]}
    selected = []
    for hypothesis in hypotheses:
        predicted = apply_hypothesis(hypothesis, test_input)
        if predicted is None:
            continue
        if predicted.cache_key() in allowed:
            selected.append(hypothesis)
    return (
        selected,
        {
            "mode": "contested_outputs_only",
            "contested": True,
            "output_uncertainty": round(uncertainty, 6),
            "selected_outputs": min(len(supports), keep_outputs),
            "selected_hypotheses": len(selected),
            "top_output_mass": round(supports[0].total_mass, 6),
            "runner_up_output_mass": round(supports[1].total_mass, 6) if len(supports) > 1 else 0.0,
        },
    )


def serialize_output_supports(supports: tuple[OutputSupport, ...]) -> tuple[dict[str, object], ...]:
    aggregate_uncertainty = round(output_uncertainty(supports), 6)
    return tuple(
        {
            "representative_hypothesis": support.best_hypothesis.description,
            "member_hypotheses": [hypothesis.description for hypothesis in support.hypotheses],
            "member_count": len(support.hypotheses),
            "total_mass": round(support.total_mass, 6),
            "normalized_mass": round(support.normalized_mass, 6),
            "margin_to_runner_up": round(support.margin_to_runner_up, 6),
            "output_uncertainty": aggregate_uncertainty,
        }
        for support in supports
    )
