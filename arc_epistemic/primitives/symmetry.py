from __future__ import annotations

import numpy as np

from arc_epistemic.utils.grid import Grid


def identity(grid: Grid) -> Grid:
    return grid.copy()


def flip_horizontal(grid: Grid) -> Grid:
    return Grid(np.fliplr(grid.array))


def flip_vertical(grid: Grid) -> Grid:
    return Grid(np.flipud(grid.array))


def rotate90(grid: Grid) -> Grid:
    return Grid(np.rot90(grid.array, k=1))


def rotate180(grid: Grid) -> Grid:
    return Grid(np.rot90(grid.array, k=2))


def rotate270(grid: Grid) -> Grid:
    return Grid(np.rot90(grid.array, k=3))
