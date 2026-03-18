from __future__ import annotations

from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.hypotheses import Hypothesis
from arc_epistemic.utils.grid import Grid


def select_top_two(hypotheses: list[Hypothesis], test_input: Grid) -> tuple[Hypothesis | None, Hypothesis | None]:
    if not hypotheses:
        return (None, None)
    first = hypotheses[0]
    first_output = apply_hypothesis(first, test_input)
    if first_output is None:
        return (None, None)
    second: Hypothesis | None = None
    for hypothesis in hypotheses[1:]:
        candidate_output = apply_hypothesis(hypothesis, test_input)
        if candidate_output is None:
            continue
        if candidate_output.cache_key() != first_output.cache_key():
            second = hypothesis
            break
    return (first, second)
