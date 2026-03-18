from __future__ import annotations

from collections.abc import Callable

from arc_epistemic.primitives.color import apply_color_map
from arc_epistemic.primitives.geometry import crop_to_content, extract_largest_object, translate_to_origin
from arc_epistemic.primitives.patterns import tile_grid
from arc_epistemic.primitives.symmetry import (
    flip_horizontal,
    flip_vertical,
    identity,
    rotate180,
    rotate270,
    rotate90,
)
from arc_epistemic.utils.grid import Grid

GridTransform = Callable[[Grid], Grid]


def named_transforms() -> list[tuple[str, GridTransform, int, bool]]:
    return [
        ("identity", identity, 0, False),
        ("flip_horizontal", flip_horizontal, 1, False),
        ("flip_vertical", flip_vertical, 1, False),
        ("rotate90", rotate90, 1, False),
        ("rotate180", rotate180, 1, False),
        ("rotate270", rotate270, 1, False),
    ]


def crop_transform(background: int | None = None) -> GridTransform:
    return lambda grid: crop_to_content(grid, background=background)


def translate_to_origin_transform(background: int | None = None) -> GridTransform:
    return lambda grid: translate_to_origin(grid, background=background)


def largest_object_transform(objects_fn: Callable[[Grid], list]) -> GridTransform:
    return lambda grid: extract_largest_object(grid, objects_fn(grid))


def color_map_transform(mapping: dict[int, int]) -> GridTransform:
    return lambda grid: apply_color_map(grid, mapping)


def tile_transform(row_factor: int, col_factor: int) -> GridTransform:
    return lambda grid: tile_grid(grid, row_factor=row_factor, col_factor=col_factor)


def compose(first: GridTransform, second: GridTransform) -> GridTransform:
    return lambda grid: second(first(grid))
