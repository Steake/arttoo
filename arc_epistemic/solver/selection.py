from __future__ import annotations

from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.hypotheses import Hypothesis
from arc_epistemic.utils.grid import Grid


def select_top_two(hypotheses: list[Hypothesis], test_input: Grid) -> tuple[Hypothesis | None, Hypothesis | None]:
    """Return the highest-ranked hypothesis that produces a valid output, and the
    next highest-ranked hypothesis that produces a distinct valid output.

    If the top-ranked hypothesis fails to apply, we continue scanning down the
    ranked list rather than discarding all remaining candidates.
    """
    if not hypotheses:
        return (None, None)
    first: Hypothesis | None = None
    first_output_key: tuple | None = None
    second: Hypothesis | None = None
    for hypothesis in hypotheses:
        candidate_output = apply_hypothesis(hypothesis, test_input)
        if candidate_output is None:
            continue
        candidate_key = candidate_output.cache_key()
        if first is None:
            first = hypothesis
            first_output_key = candidate_key
        elif candidate_key != first_output_key:
            second = hypothesis
            break
    return (first, second)
