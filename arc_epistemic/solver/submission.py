from __future__ import annotations

import json
from pathlib import Path

from arc_epistemic.utils.grid import Grid


def format_submission(predictions: dict[str, list[tuple[Grid, Grid]]]) -> dict[str, list[dict[str, list[list[int]]]]]:
    payload: dict[str, list[dict[str, list[list[int]]]]] = {}
    for task_id, attempts in sorted(predictions.items()):
        payload[task_id] = [
            {
                "attempt_1": first.to_list(),
                "attempt_2": second.to_list(),
            }
            for first, second in attempts
        ]
    return payload


def write_submission(path: str | Path, predictions: dict[str, list[tuple[Grid, Grid]]]) -> None:
    payload = format_submission(predictions)
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
