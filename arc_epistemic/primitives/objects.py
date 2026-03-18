from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from arc_epistemic.primitives.topology import connected_components
from arc_epistemic.utils.grid import BBox, Grid


@dataclass(frozen=True)
class Object:
    pixels: tuple[tuple[int, int], ...]
    color: int
    bbox: BBox

    @property
    def size(self) -> int:
        return len(self.pixels)

    @property
    def width(self) -> int:
        return self.bbox.width

    @property
    def height(self) -> int:
        return self.bbox.height

    @property
    def centroid(self) -> tuple[float, float]:
        rows = [row for row, _ in self.pixels]
        cols = [col for _, col in self.pixels]
        return (sum(rows) / len(rows), sum(cols) / len(cols))


def extract_objects(grid: Grid, background: int | None = None, connectivity: int = 4) -> list[Object]:
    bg = grid.majority_color() if background is None else background
    objects: list[Object] = []
    for color in grid.unique_colors():
        if color == bg:
            continue
        mask = grid.array == color
        for component in connected_components(mask, connectivity=connectivity):
            coords = np.argwhere(component)
            top, left = coords.min(axis=0)
            bottom, right = coords.max(axis=0)
            pixels = tuple((int(row), int(col)) for row, col in coords.tolist())
            objects.append(
                Object(
                    pixels=pixels,
                    color=int(color),
                    bbox=BBox(int(top), int(left), int(bottom), int(right)),
                )
            )
    objects.sort(key=lambda obj: (-obj.size, obj.color, obj.bbox.top, obj.bbox.left))
    return objects
