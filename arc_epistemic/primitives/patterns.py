from __future__ import annotations

import numpy as np

from arc_epistemic.utils.grid import Grid


def detect_repeat_factor(input_grid: Grid, output_grid: Grid) -> tuple[int, int] | None:
    ih, iw = input_grid.shape
    oh, ow = output_grid.shape
    if ih == 0 or iw == 0 or oh % ih or ow % iw:
        return None
    row_factor = oh // ih
    col_factor = ow // iw
    tiled = np.tile(input_grid.array, (row_factor, col_factor))
    if np.array_equal(tiled, output_grid.array):
        return (row_factor, col_factor)
    return None


def tile_grid(grid: Grid, row_factor: int, col_factor: int) -> Grid:
    return Grid(np.tile(grid.array, (row_factor, col_factor)))
