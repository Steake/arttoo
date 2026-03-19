from __future__ import annotations

import numpy as np

from arc_epistemic.utils.grid import Grid


def exact_match(predicted: Grid, expected: Grid) -> bool:
    return predicted.equals(expected)


def cell_similarity(predicted: Grid, expected: Grid) -> float:
    if predicted.shape != expected.shape:
        return 0.0
    if predicted.height == 0 or predicted.width == 0:
        return 1.0
    return float(np.mean(predicted.array == expected.array))


def shape_similarity(predicted: Grid, expected: Grid) -> float:
    ph, pw = predicted.shape
    eh, ew = expected.shape
    return 1.0 / (1.0 + abs(ph - eh) + abs(pw - ew))
