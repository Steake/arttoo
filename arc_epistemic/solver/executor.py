from __future__ import annotations

from dataclasses import dataclass

from arc_epistemic.solver.hypotheses import Hypothesis
from arc_epistemic.solver.parser import Example
from arc_epistemic.utils.grid import Grid
from arc_epistemic.utils.metrics import cell_similarity, exact_match, shape_similarity


@dataclass(frozen=True)
class EvaluationResult:
    support_count: int
    contradiction_count: int
    unresolved_count: int
    partial_credit: float
    exception_count: int
    shape_mismatch_count: int


def apply_hypothesis(hypothesis: Hypothesis, grid: Grid) -> Grid | None:
    try:
        return hypothesis.transform(grid)
    except Exception:
        return None


def evaluate_hypothesis(hypothesis: Hypothesis, train: tuple[Example, ...]) -> EvaluationResult:
    support_count = 0
    contradiction_count = 0
    unresolved_count = 0
    exception_count = 0
    shape_mismatch_count = 0
    partial_scores: list[float] = []
    for example in train:
        predicted = apply_hypothesis(hypothesis, example.input)
        if predicted is None:
            contradiction_count += 1
            exception_count += 1
            partial_scores.append(0.0)
            continue
        if exact_match(predicted, example.output):
            support_count += 1
            partial_scores.append(1.0)
            continue
        if predicted.shape != example.output.shape and not hypothesis.allows_shape_change:
            contradiction_count += 1
            shape_mismatch_count += 1
            partial_scores.append(0.0)
            continue
        similarity = 0.6 * shape_similarity(predicted, example.output) + 0.4 * cell_similarity(predicted, example.output)
        partial_scores.append(similarity)
        if similarity >= 0.3:
            unresolved_count += 1
        else:
            contradiction_count += 1
    partial_credit = sum(partial_scores) / len(partial_scores) if partial_scores else 0.0
    return EvaluationResult(
        support_count=support_count,
        contradiction_count=contradiction_count,
        unresolved_count=unresolved_count,
        partial_credit=partial_credit,
        exception_count=exception_count,
        shape_mismatch_count=shape_mismatch_count,
    )
