from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class BBox:
    top: int
    left: int
    bottom: int
    right: int

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1

    @property
    def width(self) -> int:
        return self.right - self.left + 1


class Grid:
    def __init__(self, array: np.ndarray):
        arr = np.asarray(array, dtype=int)
        if arr.ndim != 2:
            raise ValueError("Grid must be 2D")
        self.array = arr

    @classmethod
    def from_list(cls, data: list[list[int]]) -> "Grid":
        return cls(np.array(data, dtype=int))

    @property
    def height(self) -> int:
        return int(self.array.shape[0])

    @property
    def width(self) -> int:
        return int(self.array.shape[1])

    @property
    def shape(self) -> tuple[int, int]:
        return (self.height, self.width)

    def copy(self) -> "Grid":
        return Grid(self.array.copy())

    def equals(self, other: "Grid") -> bool:
        return self.shape == other.shape and np.array_equal(self.array, other.array)

    def cache_key(self) -> tuple[tuple[int, ...], ...]:
        return tuple(tuple(int(cell) for cell in row) for row in self.array.tolist())

    def unique_colors(self) -> tuple[int, ...]:
        return tuple(int(color) for color in np.unique(self.array))

    def majority_color(self) -> int:
        values, counts = np.unique(self.array, return_counts=True)
        return int(values[np.argmax(counts)])

    def bbox_for_colors(self, colors: Iterable[int] | None = None) -> BBox | None:
        if colors is None:
            mask = np.ones_like(self.array, dtype=bool)
        else:
            color_set = set(colors)
            mask = np.isin(self.array, list(color_set))
        coords = np.argwhere(mask)
        if coords.size == 0:
            return None
        top, left = coords.min(axis=0)
        bottom, right = coords.max(axis=0)
        return BBox(int(top), int(left), int(bottom), int(right))

    def content_bbox(self, background: int | None = None) -> BBox | None:
        bg = self.majority_color() if background is None else background
        coords = np.argwhere(self.array != bg)
        if coords.size == 0:
            return None
        top, left = coords.min(axis=0)
        bottom, right = coords.max(axis=0)
        return BBox(int(top), int(left), int(bottom), int(right))

    def crop(self, bbox: BBox) -> "Grid":
        return Grid(self.array[bbox.top : bbox.bottom + 1, bbox.left : bbox.right + 1].copy())

    def paste(self, other: "Grid", top: int, left: int, background: int | None = None) -> "Grid":
        canvas = self.array.copy()
        if background is not None:
            canvas.fill(background)
        bottom = top + other.height
        right = left + other.width
        if top < 0 or left < 0 or bottom > self.height or right > self.width:
            raise ValueError("Paste out of bounds")
        canvas[top:bottom, left:right] = other.array
        return Grid(canvas)

    def pad_to(self, height: int, width: int, fill: int) -> "Grid":
        if height < self.height or width < self.width:
            raise ValueError("Target size must be >= current size")
        canvas = np.full((height, width), fill, dtype=int)
        canvas[: self.height, : self.width] = self.array
        return Grid(canvas)

    def to_list(self) -> list[list[int]]:
        return self.array.tolist()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Grid) and self.equals(other)

    def __hash__(self) -> int:
        return hash(self.cache_key())

    def __repr__(self) -> str:
        return f"Grid(shape={self.shape})"
