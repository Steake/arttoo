from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from arc_epistemic.utils.grid import Grid


@dataclass(frozen=True)
class Hypothesis:
    description: str
    transform: Callable[[Grid], Grid]
    provenance: tuple[str, ...]
    complexity: int
    allows_shape_change: bool = False
    support_count: int = 0
    contradiction_count: int = 0
    unresolved_count: int = 0
    belief: float = 0.0
    disbelief: float = 0.0
    uncertainty: float = 1.0
    partial_credit: float = 0.0
    score: float = -1.0

    def with_epistemics(
        self,
        support_count: int,
        contradiction_count: int,
        unresolved_count: int,
        belief: float,
        disbelief: float,
        uncertainty: float,
        partial_credit: float,
        score: float,
    ) -> "Hypothesis":
        return replace(
            self,
            support_count=support_count,
            contradiction_count=contradiction_count,
            unresolved_count=unresolved_count,
            belief=belief,
            disbelief=disbelief,
            uncertainty=uncertainty,
            partial_credit=partial_credit,
            score=score,
        )


def primitive_hypothesis(
    description: str,
    transform: Callable[[Grid], Grid],
    family: str,
    complexity: int,
    allows_shape_change: bool = False,
) -> Hypothesis:
    return Hypothesis(
        description=description,
        transform=transform,
        provenance=(family,),
        complexity=complexity,
        allows_shape_change=allows_shape_change,
    )


def composed_hypothesis(
    description: str,
    transform: Callable[[Grid], Grid],
    left: Hypothesis,
    right_family: str,
    allows_shape_change: bool,
) -> Hypothesis:
    return Hypothesis(
        description=description,
        transform=transform,
        provenance=left.provenance + (right_family,),
        complexity=left.complexity + 2,
        allows_shape_change=left.allows_shape_change or allows_shape_change,
    )
