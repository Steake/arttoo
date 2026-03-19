from __future__ import annotations

from arc_epistemic.utils.grid import Grid


def apply_color_map(grid: Grid, mapping: dict[int, int]) -> Grid:
    out = grid.array.copy()
    for source, target in sorted(mapping.items()):
        out[grid.array == source] = target
    return Grid(out)


def infer_color_mapping(inputs: list[Grid], outputs: list[Grid]) -> dict[int, int] | None:
    mapping: dict[int, int] = {}
    for source_grid, target_grid in zip(inputs, outputs):
        if source_grid.shape != target_grid.shape:
            return None
        for source, target in zip(source_grid.array.flat, target_grid.array.flat):
            s = int(source)
            t = int(target)
            existing = mapping.get(s)
            if existing is None:
                mapping[s] = t
            elif existing != t:
                return None
    return mapping if mapping else None
