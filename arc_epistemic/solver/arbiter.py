from __future__ import annotations

from arc_epistemic.solver.hypotheses import Hypothesis


def rank_hypotheses(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    return sorted(
        hypotheses,
        key=lambda hypothesis: (
            -hypothesis.score,
            hypothesis.contradiction_count,
            hypothesis.complexity,
            hypothesis.description,
        ),
    )
