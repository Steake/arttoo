from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from arc_epistemic.solver.parser import Task, parse_task
from arc_epistemic.utils.grid import Grid


@dataclass(frozen=True)
class FixtureTask:
    task_id: str
    task: Task
    expected_outputs: tuple[Grid, ...]
    ranking_prefix: tuple[str, ...]
    notes: str
    expect_exact: bool
    failure_tags: tuple[str, ...]


def _load_fixture(path: Path) -> FixtureTask:
    payload = json.loads(path.read_text(encoding="utf-8"))
    task_id = payload.get("task_id", path.stem)
    task = parse_task(task_id, payload)
    golden = payload.get("golden", {})
    expected_outputs = tuple(Grid.from_list(grid) for grid in golden.get("expected_test_outputs", []))
    ranking_prefix = tuple(golden.get("ranking_prefix", []))
    notes = golden.get("notes", "")
    expect_exact = bool(golden.get("expect_exact", True))
    failure_tags = tuple(golden.get("failure_tags", []))
    return FixtureTask(
        task_id=task_id,
        task=task,
        expected_outputs=expected_outputs,
        ranking_prefix=ranking_prefix,
        notes=notes,
        expect_exact=expect_exact,
        failure_tags=failure_tags,
    )


def load_fixture_tasks(directory: str | Path) -> list[FixtureTask]:
    root = Path(directory)
    fixtures = [_load_fixture(path) for path in sorted(root.glob("*.json"))]
    return fixtures


def discover_splits(split_directory: str | Path) -> tuple[str, ...]:
    root = Path(split_directory)
    return tuple(sorted(path.stem for path in root.glob("*.json")))


def load_fixture_split(
    directory: str | Path,
    split: str = "all",
    split_directory: str | Path = "data/splits",
) -> list[FixtureTask]:
    fixtures = load_fixture_tasks(directory)
    if split == "all":
        return fixtures
    root = Path(split_directory)
    split_path = root / f"{split}.json"
    if not split_path.exists():
        raise FileNotFoundError(f"Unknown split: {split}")
    task_ids = set(json.loads(split_path.read_text(encoding="utf-8"))["task_ids"])
    return [fixture for fixture in fixtures if fixture.task_id in task_ids]
