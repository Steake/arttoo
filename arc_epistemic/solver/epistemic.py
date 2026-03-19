from __future__ import annotations


def derive_epistemic_state(
    total_pairs: int,
    support_count: int,
    contradiction_count: int,
    unresolved_count: int,
    partial_credit: float,
) -> tuple[float, float, float, float]:
    if total_pairs <= 0:
        return (0.0, 0.0, 1.0, -1.0)
    belief = support_count / total_pairs
    disbelief = contradiction_count / total_pairs
    uncertainty = max(0.0, unresolved_count / total_pairs)
    score = belief + 0.15 * partial_credit - 0.5 * uncertainty - disbelief
    return (belief, disbelief, uncertainty, score)
