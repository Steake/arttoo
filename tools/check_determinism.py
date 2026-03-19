from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.analysis import evaluate_fixture_batch, serialize_json
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.reporting import determinism_markdown, write_json
from arc_epistemic.solver.agents import FULL_COAGENCY_CONFIG


def _digest(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_output_payload(batch: dict[str, object]) -> list[tuple[object, ...]]:
    return sorted(
        [
        (item["task_id"], item["attempt_1"], item["attempt_2"], item["telemetry"]["deterministic_fingerprint"])
        for item in batch["per_task"]
        ]
    )


def _stable_metric_payload(batch: dict[str, object]) -> dict[str, object]:
    aggregate = dict(batch["aggregate"])
    aggregate.pop("average_runtime_ms", None)
    aggregate.pop("max_runtime_ms", None)
    aggregate.pop("generated_at_utc", None)
    return aggregate


def _ranking_payload(batch: dict[str, object]) -> list[tuple[object, ...]]:
    return sorted(
        [
        (
            item["task_id"],
            item["winning_hypothesis"],
            item["second_hypothesis"],
            [entry["description"] for entry in item["telemetry"]["final_ranking"][:5]],
        )
        for item in batch["per_task"]
        ]
    )


def _subprocess_batch(tasks: str, split: str, repo_root: Path, seed: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "benchmark.json"
        env = dict(os.environ)
        env["ARC_EPISTEMIC_SEED"] = str(seed)
        subprocess.run(
            [
                "python",
                "tools/run_benchmarks.py",
                "--tasks",
                tasks,
                "--split",
                split,
                "--report",
                str(Path(tmpdir) / "benchmark.md"),
                "--json",
                str(json_path),
            ],
            cwd=str(repo_root),
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        return json.loads(json_path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check solver determinism across repeated runs.")
    parser.add_argument("--tasks", required=True, help="Directory of ARC fixture tasks.")
    parser.add_argument("--split", default="all", help="Task split to evaluate.")
    parser.add_argument("--runs", required=True, type=int, help="Number of repeated runs.")
    parser.add_argument("--report", help="Markdown determinism report output path.")
    parser.add_argument("--json", help="Optional JSON determinism output path.")
    args = parser.parse_args(argv)

    fixtures = load_fixture_split(args.tasks, split=args.split)
    repeated_batches = [evaluate_fixture_batch(fixtures, FULL_COAGENCY_CONFIG, split=args.split) for _ in range(args.runs)]
    reversed_batches = [
        evaluate_fixture_batch(list(reversed(fixtures)), FULL_COAGENCY_CONFIG, split=args.split)
        for _ in range(max(1, min(2, args.runs)))
    ]
    repo_root = Path(__file__).resolve().parents[1]
    subprocess_batches = [_subprocess_batch(args.tasks, args.split, repo_root, seed) for seed in range(2)]

    output_digests = [_digest(_stable_output_payload(batch)) for batch in repeated_batches + reversed_batches + subprocess_batches]
    metric_digests = [_digest(_stable_metric_payload(batch)) for batch in repeated_batches + reversed_batches + subprocess_batches]
    ranking_digests = [_digest(_ranking_payload(batch)) for batch in repeated_batches + reversed_batches + subprocess_batches]
    stable_outputs = len(set(output_digests)) == 1
    stable_rankings = len(set(ranking_digests)) == 1
    stable_metrics = len(set(metric_digests)) == 1

    baseline = repeated_batches[0]
    nondeterministic_tasks = set()
    baseline_outputs = {item["task_id"]: item for item in baseline["per_task"]}
    for batch in repeated_batches[1:] + reversed_batches + subprocess_batches:
        for item in batch["per_task"]:
            reference = baseline_outputs[item["task_id"]]
            if (
                reference["attempt_1"] != item["attempt_1"]
                or reference["attempt_2"] != item["attempt_2"]
                or reference["winning_hypothesis"] != item["winning_hypothesis"]
                or reference["second_hypothesis"] != item["second_hypothesis"]
                or reference["telemetry"]["deterministic_fingerprint"] != item["telemetry"]["deterministic_fingerprint"]
            ):
                nondeterministic_tasks.add(item["task_id"])

    result = {
        "split": args.split,
        "runs": args.runs,
        "checked_shuffled_order": True,
        "checked_process_restarts": True,
        "checked_seed_perturbations": True,
        "stable_outputs": stable_outputs,
        "stable_rankings": stable_rankings,
        "stable_metrics": stable_metrics,
        "nondeterministic_tasks": sorted(nondeterministic_tasks),
    }
    report_path = args.report or "reports/determinism.md"
    json_path = args.json or str(Path(report_path).with_suffix(".json"))
    write_json(json_path, serialize_json(result))
    write_json(report_path, determinism_markdown(result))
    return 0 if stable_outputs and stable_rankings and stable_metrics else 1


if __name__ == "__main__":
    raise SystemExit(main())
