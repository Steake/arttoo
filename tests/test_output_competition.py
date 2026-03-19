from __future__ import annotations

import unittest

from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.eval.output_competition import (
    run_frozen_output_competition_experiment,
    run_native_output_competition_experiment,
)
from arc_epistemic.solver.hypotheses import primitive_hypothesis
from arc_epistemic.solver.output_competition import (
    aggregate_output_support,
    output_uncertainty,
    select_contested_hypotheses,
    select_top_two_output_classes,
)
from arc_epistemic.utils.grid import Grid


def _constant_grid(grid_data: list[list[int]]):
    output = Grid.from_list(grid_data)
    return lambda _: output.copy()


def _scored_hypothesis(
    description: str,
    grid_data: list[list[int]],
    *,
    belief: float,
    disbelief: float,
    uncertainty: float,
    partial_credit: float,
    score: float,
):
    return primitive_hypothesis(description, _constant_grid(grid_data), family="test", complexity=1).with_epistemics(
        support_count=1,
        contradiction_count=0,
        unresolved_count=0,
        belief=belief,
        disbelief=disbelief,
        uncertainty=uncertainty,
        partial_credit=partial_credit,
        score=score,
    )


class OutputCompetitionUnitTests(unittest.TestCase):
    def test_output_aggregation_prefers_shared_output_mass(self) -> None:
        wrong = _scored_hypothesis(
            "wrong_top",
            [[1]],
            belief=0.7,
            disbelief=0.0,
            uncertainty=0.0,
            partial_credit=0.2,
            score=0.9,
        )
        correct_a = _scored_hypothesis(
            "correct_a",
            [[2]],
            belief=0.45,
            disbelief=0.0,
            uncertainty=0.3,
            partial_credit=0.5,
            score=0.6,
        )
        correct_b = _scored_hypothesis(
            "correct_b",
            [[2]],
            belief=0.4,
            disbelief=0.0,
            uncertainty=0.4,
            partial_credit=0.5,
            score=0.59,
        )
        first, second, supports = select_top_two_output_classes(
            [wrong, correct_a, correct_b],
            Grid.from_list([[0]]),
        )
        self.assertEqual(first.description, "correct_a")
        self.assertEqual(second.description, "wrong_top")
        self.assertEqual(len(supports[0].hypotheses), 2)
        self.assertGreater(supports[0].total_mass, supports[1].total_mass)

    def test_output_uncertainty_tracks_contested_classes(self) -> None:
        a = _scored_hypothesis("a", [[1]], belief=0.4, disbelief=0.0, uncertainty=0.2, partial_credit=0.4, score=0.5)
        b = _scored_hypothesis("b", [[2]], belief=0.39, disbelief=0.0, uncertainty=0.2, partial_credit=0.4, score=0.49)
        supports = aggregate_output_support([a, b], Grid.from_list([[0]]))
        self.assertGreater(output_uncertainty(supports), 0.9)

    def test_contested_refinement_gate_keeps_only_close_output_classes(self) -> None:
        top_a = _scored_hypothesis("top_a", [[1]], belief=0.5, disbelief=0.0, uncertainty=0.2, partial_credit=0.5, score=0.6)
        top_b = _scored_hypothesis("top_b", [[1]], belief=0.45, disbelief=0.0, uncertainty=0.2, partial_credit=0.5, score=0.59)
        runner_up = _scored_hypothesis("runner_up", [[2]], belief=0.7, disbelief=0.0, uncertainty=0.1, partial_credit=0.1, score=0.75)
        loser = _scored_hypothesis("loser", [[3]], belief=0.1, disbelief=0.2, uncertainty=0.5, partial_credit=0.2, score=0.05)
        selected, gate = select_contested_hypotheses(
            [runner_up, top_a, top_b, loser],
            Grid.from_list([[0]]),
            margin_threshold=0.5,
            keep_outputs=2,
        )
        self.assertTrue(gate["contested"])
        self.assertEqual({hypothesis.description for hypothesis in selected}, {"runner_up", "top_a", "top_b"})


class OutputCompetitionExperimentSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_fixture_split("data/fixtures", split="blind_holdout_v3")

    def test_frozen_output_competition_report_has_expected_fields(self) -> None:
        report = run_frozen_output_competition_experiment(self.fixtures, split="blind_holdout_v3")
        self.assertEqual(report["subset"], "ranking_conflict")
        self.assertEqual(report["task_count"], 8)
        self.assertIn("single_best_solve_rate", report)
        self.assertIn("output_aggregation_solve_rate", report)
        self.assertIn("tasks", report)

    def test_native_output_competition_report_has_efficiency_fields(self) -> None:
        report = run_native_output_competition_experiment(self.fixtures, split="blind_holdout_v3")
        self.assertEqual(report["subset"], "ranking_conflict")
        self.assertEqual(report["task_count"], 8)
        self.assertIn("gated_compute_savings_vs_aggregated", report)
        self.assertIn("tasks_flagged_contested", report)
        self.assertIn("tasks", report)


if __name__ == "__main__":
    unittest.main()
