from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from arc_epistemic.eval.fixtures import FixtureTask
from arc_epistemic.solver.agents import FULL_COAGENCY_CONFIG, SolverConfig
from arc_epistemic.solver.output_competition import output_uncertainty, select_top_two_output_classes
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.solver.solver import solve_task_with_diagnostics


OUTPUT_AGGREGATION_CONFIG = SolverConfig(
    name="output_aggregation_broad_refinement",
    use_epistemic_scoring=True,
    use_refinement=True,
    use_output_aggregation=True,
    use_margin_gated_refinement=False,
)

OUTPUT_AGGREGATION_GATED_CONFIG = SolverConfig(
    name="output_aggregation_contested_refinement",
    use_epistemic_scoring=True,
    use_refinement=True,
    use_output_aggregation=True,
    use_margin_gated_refinement=True,
)


@dataclass(frozen=True)
class FrozenSelectionRow:
    task_id: str
    solved_single_best: bool
    solved_output_aggregation: bool
    single_best_hypothesis: str
    output_winner_hypothesis: str
    winner_changed: bool
    output_uncertainty: float
    top_output_support_count: int


@dataclass(frozen=True)
class NativeSelectionRow:
    task_id: str
    baseline_solved: bool
    aggregated_solved: bool
    gated_solved: bool
    baseline_evaluations: int
    aggregated_evaluations: int
    gated_evaluations: int
    baseline_refined: int
    aggregated_refined: int
    gated_refined: int
    gated_contested: bool
    gated_output_uncertainty: float


def _matches_expected(predicted, expected) -> bool:
    return predicted is not None and predicted.cache_key() == expected.cache_key()


def _ranking_conflict_fixtures(fixtures: list[FixtureTask]) -> list[FixtureTask]:
    return [fixture for fixture in fixtures if "ranking_conflict" in fixture.task_id]


def run_frozen_output_competition_experiment(
    fixtures: list[FixtureTask],
    split: str,
) -> dict[str, Any]:
    rows: list[FrozenSelectionRow] = []
    for fixture in _ranking_conflict_fixtures(fixtures):
        result = solve_task_with_diagnostics(fixture.task, config=FULL_COAGENCY_CONFIG)
        ranked = result.ranked_hypotheses
        test_input = fixture.task.test[0].input
        expected = fixture.expected_outputs[0]
        single_best, _ = select_top_two(ranked, test_input)
        aggregated, _, supports = select_top_two_output_classes(ranked, test_input)
        single_grid = result.predictions[0][0] if ranked else None
        aggregated_grid = supports[0].output if supports else None
        rows.append(
            FrozenSelectionRow(
                task_id=fixture.task_id,
                solved_single_best=_matches_expected(single_grid, expected),
                solved_output_aggregation=_matches_expected(aggregated_grid, expected),
                single_best_hypothesis=single_best.description if single_best else "",
                output_winner_hypothesis=aggregated.description if aggregated else "",
                winner_changed=bool(single_best and aggregated and single_best.description != aggregated.description),
                output_uncertainty=round(output_uncertainty(supports), 6),
                top_output_support_count=len(supports[0].hypotheses) if supports else 0,
            )
        )
    single_solved = sum(1 for row in rows if row.solved_single_best)
    aggregated_solved = sum(1 for row in rows if row.solved_output_aggregation)
    return {
        "split": split,
        "subset": "ranking_conflict",
        "task_count": len(rows),
        "single_best_solve_rate": round((single_solved / len(rows)) if rows else 0.0, 4),
        "output_aggregation_solve_rate": round((aggregated_solved / len(rows)) if rows else 0.0, 4),
        "solve_rate_lift": round(((aggregated_solved - single_solved) / len(rows)) if rows else 0.0, 4),
        "winner_changes": sum(1 for row in rows if row.winner_changed),
        "tasks_with_nonzero_output_uncertainty": sum(1 for row in rows if row.output_uncertainty > 0.0),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tasks": [asdict(row) for row in rows],
    }


def run_native_output_competition_experiment(
    fixtures: list[FixtureTask],
    split: str,
) -> dict[str, Any]:
    rows: list[NativeSelectionRow] = []
    ranked_conflict = _ranking_conflict_fixtures(fixtures)
    for fixture in ranked_conflict:
        baseline = solve_task_with_diagnostics(fixture.task, config=FULL_COAGENCY_CONFIG)
        aggregated = solve_task_with_diagnostics(fixture.task, config=OUTPUT_AGGREGATION_CONFIG)
        gated = solve_task_with_diagnostics(fixture.task, config=OUTPUT_AGGREGATION_GATED_CONFIG)
        expected = fixture.expected_outputs[0]
        rows.append(
            NativeSelectionRow(
                task_id=fixture.task_id,
                baseline_solved=_matches_expected(baseline.predictions[0][0], expected),
                aggregated_solved=_matches_expected(aggregated.predictions[0][0], expected),
                gated_solved=_matches_expected(gated.predictions[0][0], expected),
                baseline_evaluations=baseline.loop_diagnostics.evaluation_count,
                aggregated_evaluations=aggregated.loop_diagnostics.evaluation_count,
                gated_evaluations=gated.loop_diagnostics.evaluation_count,
                baseline_refined=baseline.loop_diagnostics.refined_count,
                aggregated_refined=aggregated.loop_diagnostics.refined_count,
                gated_refined=gated.loop_diagnostics.refined_count,
                gated_contested=bool(gated.loop_diagnostics.refinement_gate.get("contested", False)),
                gated_output_uncertainty=float(gated.selection_telemetry.get("output_uncertainty", 1.0)),
            )
        )
    total = len(rows)
    return {
        "split": split,
        "subset": "ranking_conflict",
        "task_count": total,
        "baseline_solve_rate": round((sum(1 for row in rows if row.baseline_solved) / total) if total else 0.0, 4),
        "output_aggregation_solve_rate": round((sum(1 for row in rows if row.aggregated_solved) / total) if total else 0.0, 4),
        "gated_output_aggregation_solve_rate": round((sum(1 for row in rows if row.gated_solved) / total) if total else 0.0, 4),
        "mean_baseline_evaluations": round((sum(row.baseline_evaluations for row in rows) / total) if total else 0.0, 4),
        "mean_aggregated_evaluations": round((sum(row.aggregated_evaluations for row in rows) / total) if total else 0.0, 4),
        "mean_gated_evaluations": round((sum(row.gated_evaluations for row in rows) / total) if total else 0.0, 4),
        "mean_baseline_refined": round((sum(row.baseline_refined for row in rows) / total) if total else 0.0, 4),
        "mean_aggregated_refined": round((sum(row.aggregated_refined for row in rows) / total) if total else 0.0, 4),
        "mean_gated_refined": round((sum(row.gated_refined for row in rows) / total) if total else 0.0, 4),
        "gated_compute_savings_vs_aggregated": round(
            ((sum(row.aggregated_evaluations for row in rows) - sum(row.gated_evaluations for row in rows)) / total) if total else 0.0,
            4,
        ),
        "tasks_flagged_contested": sum(1 for row in rows if row.gated_contested),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tasks": [asdict(row) for row in rows],
    }


def output_competition_markdown(bundle: dict[str, Any]) -> str:
    frozen = bundle["frozen"]
    native = bundle["native"]
    return "\n".join(
        [
            "# Output Competition Benchmark",
            "",
            f"**Split**: `{bundle['split']}` | **Subset**: `{frozen['subset']}`",
            "",
            "## Frozen Candidate Pool",
            "",
            f"- Single-best solve rate: `{frozen['single_best_solve_rate']:.3f}`",
            f"- Output-aggregation solve rate: `{frozen['output_aggregation_solve_rate']:.3f}`",
            f"- Solve-rate lift: `{frozen['solve_rate_lift']:+.3f}`",
            f"- Winner changes: `{frozen['winner_changes']}`",
            f"- Tasks with non-zero output uncertainty: `{frozen['tasks_with_nonzero_output_uncertainty']}`",
            "",
            "## Native Pipeline",
            "",
            f"- Baseline solve rate: `{native['baseline_solve_rate']:.3f}`",
            f"- Output-aggregation solve rate: `{native['output_aggregation_solve_rate']:.3f}`",
            f"- Gated output-aggregation solve rate: `{native['gated_output_aggregation_solve_rate']:.3f}`",
            f"- Mean evaluations baseline / aggregated / gated: `{native['mean_baseline_evaluations']:.1f}` / `{native['mean_aggregated_evaluations']:.1f}` / `{native['mean_gated_evaluations']:.1f}`",
            f"- Mean refined baseline / aggregated / gated: `{native['mean_baseline_refined']:.1f}` / `{native['mean_aggregated_refined']:.1f}` / `{native['mean_gated_refined']:.1f}`",
            f"- Gated compute savings vs aggregated: `{native['gated_compute_savings_vs_aggregated']:+.1f}`",
            f"- Tasks flagged contested: `{native['tasks_flagged_contested']}`",
        ]
    )


def output_competition_json(bundle: dict[str, Any]) -> str:
    return json.dumps(bundle, indent=2, sort_keys=True)
