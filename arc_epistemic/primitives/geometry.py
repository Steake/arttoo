from __future__ import annotations

import numpy as np

from arc_epistemic.primitives.objects import Object
from arc_epistemic.utils.grid import Grid


def crop_to_content(grid: Grid, background: int | None = None) -> Grid:
    bbox = grid.content_bbox(background=background)
    if bbox is None:
        return grid.copy()
    return grid.crop(bbox)


def extract_largest_object(grid: Grid, objects: list[Object], background: int | None = None) -> Grid:
    if not objects:
        return grid.copy()
    bg = grid.majority_color() if background is None else background
    obj = objects[0]
    canvas = np.full((obj.height, obj.width), bg, dtype=int)
    for row, col in obj.pixels:
        canvas[row - obj.bbox.top, col - obj.bbox.left] = obj.color
    return Grid(canvas)


def translate_to_origin(grid: Grid, background: int | None = None) -> Grid:
    bbox = grid.content_bbox(background=background)
    if bbox is None:
        return grid.copy()
    cropped = grid.crop(bbox)
    canvas = np.full(grid.shape, grid.majority_color() if background is None else background, dtype=int)
    canvas[: cropped.height, : cropped.width] = cropped.array
    return Grid(canvas)
