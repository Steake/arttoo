from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arc_epistemic.utils.grid import Grid


@dataclass(frozen=True)
class Example:
    input: Grid
    output: Grid


@dataclass(frozen=True)
class TestCase:
    input: Grid


@dataclass(frozen=True)
class Task:
    task_id: str
    train: tuple[Example, ...]
    test: tuple[TestCase, ...]


def _to_grid(data: list[list[int]]) -> Grid:
    return Grid.from_list(data)


def parse_task(task_id: str, payload: dict[str, Any]) -> Task:
    train = tuple(
        Example(input=_to_grid(example["input"]), output=_to_grid(example["output"]))
        for example in payload.get("train", [])
    )
    test = tuple(TestCase(input=_to_grid(example["input"])) for example in payload.get("test", []))
    return Task(task_id=task_id, train=train, test=test)


def load_tasks(path: str | Path) -> dict[str, Task]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "train" in payload and "test" in payload:
        task = parse_task(Path(path).stem, payload)
        return {task.task_id: task}
    return {task_id: parse_task(task_id, task_payload) for task_id, task_payload in sorted(payload.items())}
