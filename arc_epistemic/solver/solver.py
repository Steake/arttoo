from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from arc_epistemic.solver.agents import FULL_COAGENCY_CONFIG, LoopDiagnostics, SolverConfig, run_coagency_loop
from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.hypotheses import Hypothesis
from arc_epistemic.solver.output_competition import (
    output_entropy,
    output_margin,
    output_uncertainty,
    select_top_two_diversity_aware_output_classes,
    select_top_two_output_classes,
    serialize_output_supports,
)
from arc_epistemic.solver.parser import Task, load_tasks
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.solver.submission import write_submission


@dataclass(frozen=True)
class SolveResult:
    predictions: list[tuple]
    ranked_hypotheses: list[Hypothesis]
    loop_diagnostics: LoopDiagnostics
    selected_hypotheses: tuple[str, ...]
    selection_telemetry: dict[str, object]
    run_fingerprint: str


def _fingerprint(predictions: list[tuple], ranked: list[Hypothesis]) -> str:
    payload = {
        "predictions": [
            {"attempt_1": first.to_list(), "attempt_2": second.to_list()}
            for first, second in predictions
        ],
        "ranking": [hypothesis.description for hypothesis in ranked],
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def solve_task_with_diagnostics(task: Task, config: SolverConfig = FULL_COAGENCY_CONFIG) -> SolveResult:
    loop_result = run_coagency_loop(task, config=config)
    ranked = loop_result.ranked_hypotheses
    predictions = []
    selected_hypotheses: list[str] = []
    selection_telemetry: dict[str, object] = {"mode": "single_best_hypothesis"}
    for test_case in task.test:
        if config.use_output_aggregation and config.use_diversity_aware_output_selection:
            first_hypothesis, second_hypothesis, supports = select_top_two_diversity_aware_output_classes(ranked, test_case.input)
            selection_telemetry = {
                "mode": "output_aggregation_diversity",
                "output_supports": list(serialize_output_supports(supports)),
                "output_uncertainty": round(output_uncertainty(supports), 6),
                "output_entropy": round(output_entropy(supports), 6),
                "output_margin": round(output_margin(supports), 6),
                "winner_changed_vs_single_best": bool(
                    ranked and first_hypothesis and ranked[0].description != first_hypothesis.description
                ),
            }
        elif config.use_output_aggregation:
            first_hypothesis, second_hypothesis, supports = select_top_two_output_classes(ranked, test_case.input)
            selection_telemetry = {
                "mode": "output_aggregation",
                "output_supports": list(serialize_output_supports(supports)),
                "output_uncertainty": round(output_uncertainty(supports), 6),
                "output_entropy": round(output_entropy(supports), 6),
                "output_margin": round(output_margin(supports), 6),
                "winner_changed_vs_single_best": bool(
                    ranked and first_hypothesis and ranked[0].description != first_hypothesis.description
                ),
            }
        else:
            first_hypothesis, second_hypothesis = select_top_two(ranked, test_case.input)
        if first_hypothesis is None:
            fallback = test_case.input.copy()
            predictions.append((fallback, fallback))
            selected_hypotheses.extend(["", ""])
            continue
        attempt_1 = apply_hypothesis(first_hypothesis, test_case.input) or test_case.input.copy()
        selected_hypotheses.append(first_hypothesis.description)
        if second_hypothesis is None:
            attempt_2 = test_case.input.copy()
            if attempt_2.cache_key() == attempt_1.cache_key():
                attempt_2 = attempt_1.copy()
            selected_hypotheses.append("")
        else:
            attempt_2 = apply_hypothesis(second_hypothesis, test_case.input) or attempt_1.copy()
            if attempt_2.cache_key() == attempt_1.cache_key():
                attempt_2 = attempt_1.copy()
            selected_hypotheses.append(second_hypothesis.description)
        predictions.append((attempt_1, attempt_2))
    return SolveResult(
        predictions=predictions,
        ranked_hypotheses=ranked,
        loop_diagnostics=loop_result.diagnostics,
        selected_hypotheses=tuple(selected_hypotheses),
        selection_telemetry=selection_telemetry,
        run_fingerprint=_fingerprint(predictions, ranked),
    )


def solve_task(task: Task, config: SolverConfig = FULL_COAGENCY_CONFIG):
    return solve_task_with_diagnostics(task, config=config).predictions


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ARC epistemic solver.")
    parser.add_argument("--input", required=True, help="Path to ARC JSON task file.")
    parser.add_argument("--output", required=True, help="Path to output submission JSON.")
    args = parser.parse_args(argv)

    tasks = load_tasks(args.input)
    predictions = {task_id: solve_task(task, config=FULL_COAGENCY_CONFIG) for task_id, task in tasks.items()}
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_submission(output_path, predictions)
    return 0
