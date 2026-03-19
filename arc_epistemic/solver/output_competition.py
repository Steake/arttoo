from __future__ import annotations

from dataclasses import dataclass
from math import log

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
    family_diversity_count: int
    lineage_diversity_count: int
    dominant_family_share: float
    dominant_hypothesis_share: float
    diversity_adjusted_mass: float


def evidence_mass(hypothesis: Hypothesis) -> float:
    """Deterministic non-negative support for output-level aggregation."""
    return max(0.0, hypothesis.belief + 0.5 * hypothesis.partial_credit - hypothesis.disbelief)


def _family_key(hypothesis: Hypothesis) -> str:
    return hypothesis.provenance[0] if hypothesis.provenance else "unknown"


def _lineage_key(hypothesis: Hypothesis) -> tuple[str, ...]:
    return hypothesis.provenance or ("unknown",)


def diversity_adjusted_mass(
    total_mass: float,
    *,
    family_diversity_count: int,
    lineage_diversity_count: int,
    dominant_family_share: float,
    dominant_hypothesis_share: float,
) -> float:
    """Conservative diversity-aware coalition score.

    Extra support is granted only for distinct root families; lineage variation
    within the same family gets a small bonus. Highly concentrated coalitions are
    penalized so a single brittle family cannot dominate by raw mass alone.
    """
    multiplier = (
        1.0
        + 0.50 * max(0, family_diversity_count - 1)
        + 0.05 * max(0, lineage_diversity_count - family_diversity_count)
        - 0.60 * dominant_family_share
        - 0.20 * dominant_hypothesis_share
    )
    return total_mass * max(0.25, multiplier)


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
        family_masses: dict[str, float] = {}
        lineage_masses: dict[tuple[str, ...], float] = {}
        member_masses: list[float] = []
        for hypothesis in payload["hypotheses"]:
            hypothesis_mass = evidence_mass(hypothesis)
            member_masses.append(hypothesis_mass)
            family_key = _family_key(hypothesis)
            family_masses[family_key] = family_masses.get(family_key, 0.0) + hypothesis_mass
            lineage_key = _lineage_key(hypothesis)
            lineage_masses[lineage_key] = lineage_masses.get(lineage_key, 0.0) + hypothesis_mass
        dominant_family_share = (max(family_masses.values()) / mass) if mass > 0.0 and family_masses else 1.0
        dominant_hypothesis_share = (max(member_masses) / mass) if mass > 0.0 and member_masses else 1.0
        supports.append(
            OutputSupport(
                key=key,
                output=payload["output"],
                hypotheses=tuple(payload["hypotheses"]),
                total_mass=mass,
                normalized_mass=normalized,
                margin_to_runner_up=margin,
                best_hypothesis=payload["best_hypothesis"],
                family_diversity_count=len(family_masses),
                lineage_diversity_count=len(lineage_masses),
                dominant_family_share=dominant_family_share,
                dominant_hypothesis_share=dominant_hypothesis_share,
                diversity_adjusted_mass=diversity_adjusted_mass(
                    mass,
                    family_diversity_count=len(family_masses),
                    lineage_diversity_count=len(lineage_masses),
                    dominant_family_share=dominant_family_share,
                    dominant_hypothesis_share=dominant_hypothesis_share,
                ),
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


def output_entropy(supports: tuple[OutputSupport, ...]) -> float:
    if not supports:
        return 1.0
    if len(supports) == 1:
        return 0.0
    masses = [support.normalized_mass for support in supports if support.normalized_mass > 0.0]
    if not masses:
        return 1.0
    entropy = -sum(probability * log(probability) for probability in masses)
    return entropy / log(len(supports))


def output_margin(supports: tuple[OutputSupport, ...]) -> float:
    if len(supports) < 2:
        return 1.0
    return max(0.0, supports[0].normalized_mass - supports[1].normalized_mass)


def rank_output_classes(
    hypotheses: list[Hypothesis],
    test_input: Grid,
    *,
    strategy: str = "mass",
) -> tuple[OutputSupport, ...]:
    supports = aggregate_output_support(hypotheses, test_input)
    if strategy == "mass":
        return supports
    if strategy == "diversity":
        return tuple(
            sorted(
                supports,
                key=lambda support: (
                    -support.diversity_adjusted_mass,
                    -support.total_mass,
                    -support.best_hypothesis.score,
                    support.best_hypothesis.contradiction_count,
                    support.best_hypothesis.complexity,
                    support.best_hypothesis.description,
                ),
            )
        )
    raise ValueError(f"Unknown output ranking strategy: {strategy}")


def select_top_two_output_classes(
    hypotheses: list[Hypothesis],
    test_input: Grid,
) -> tuple[Hypothesis | None, Hypothesis | None, tuple[OutputSupport, ...]]:
    supports = rank_output_classes(hypotheses, test_input, strategy="mass")
    if not supports:
        return (None, None, tuple())
    first = supports[0].best_hypothesis
    second = supports[1].best_hypothesis if len(supports) > 1 else None
    return (first, second, supports)


def select_top_two_diversity_aware_output_classes(
    hypotheses: list[Hypothesis],
    test_input: Grid,
) -> tuple[Hypothesis | None, Hypothesis | None, tuple[OutputSupport, ...]]:
    supports = rank_output_classes(hypotheses, test_input, strategy="diversity")
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
    entropy_threshold: float = 0.55,
    strategy: str = "mass",
) -> tuple[list[Hypothesis], dict[str, object]]:
    supports = rank_output_classes(hypotheses, test_input, strategy=strategy)
    if not supports:
        return (
            hypotheses,
            {
                "mode": "no_outputs",
                "contested": False,
                "output_uncertainty": 1.0,
                "output_entropy": 1.0,
                "output_margin": 0.0,
                "selected_outputs": 0,
                "selected_hypotheses": len(hypotheses),
            },
        )
    uncertainty = output_uncertainty(supports)
    entropy = output_entropy(supports)
    margin = output_margin(supports)
    contested = len(supports) > 1 and (uncertainty >= margin_threshold or entropy >= entropy_threshold)
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
                "output_entropy": round(entropy, 6),
                "output_margin": round(margin, 6),
                "selected_outputs": 1,
                "selected_hypotheses": len(selected),
                "top_output_mass": round(supports[0].total_mass, 6),
                "strategy": strategy,
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
                "output_entropy": round(entropy, 6),
                "output_margin": round(margin, 6),
                "selected_outputs": min(len(supports), keep_outputs),
                "selected_hypotheses": len(selected),
                "top_output_mass": round(supports[0].total_mass, 6),
                "runner_up_output_mass": round(supports[1].total_mass, 6) if len(supports) > 1 else 0.0,
                "strategy": strategy,
            },
        )


def serialize_output_supports(supports: tuple[OutputSupport, ...]) -> tuple[dict[str, object], ...]:
    aggregate_uncertainty = round(output_uncertainty(supports), 6)
    aggregate_entropy = round(output_entropy(supports), 6)
    aggregate_margin = round(output_margin(supports), 6)
    return tuple(
        {
            "output_fingerprint": support.output.fingerprint(),
            "representative_hypothesis": support.best_hypothesis.description,
            "member_hypotheses": [hypothesis.description for hypothesis in support.hypotheses],
            "member_details": [
                {
                    "description": hypothesis.description,
                    "evidence_mass": round(evidence_mass(hypothesis), 6),
                    "normalized_within_output": round((evidence_mass(hypothesis) / support.total_mass), 6)
                    if support.total_mass > 0.0
                    else 0.0,
                    "root_family": _family_key(hypothesis),
                    "lineage": list(_lineage_key(hypothesis)),
                }
                for hypothesis in support.hypotheses
            ],
            "member_count": len(support.hypotheses),
            "total_mass": round(support.total_mass, 6),
            "diversity_adjusted_mass": round(support.diversity_adjusted_mass, 6),
            "normalized_mass": round(support.normalized_mass, 6),
            "margin_to_runner_up": round(support.margin_to_runner_up, 6),
            "output_uncertainty": aggregate_uncertainty,
            "output_entropy": aggregate_entropy,
            "output_margin": aggregate_margin,
            "family_diversity_count": support.family_diversity_count,
            "lineage_diversity_count": support.lineage_diversity_count,
            "dominant_family_share": round(support.dominant_family_share, 6),
            "dominant_hypothesis_share": round(support.dominant_hypothesis_share, 6),
        }
        for support in supports
    )
