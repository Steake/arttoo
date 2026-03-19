"""Tests for epistemic reordering analysis and thesis validation tooling."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.solver.agents import FULL_COAGENCY_CONFIG, PRIMITIVE_BASELINE_CONFIG, run_coagency_loop
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.solver.executor import apply_hypothesis


class ReorderingDetectionTests(unittest.TestCase):
    """Verify that composition tasks produce first-pass → final reorderings."""

    def _check_reordering(self, task_id: str, split: str, expect_reordering: bool) -> None:
        fixtures = load_fixture_split("data/fixtures", split)
        fixture = next((f for f in fixtures if f.task_id == task_id), None)
        self.assertIsNotNone(fixture, f"Fixture {task_id!r} not found in split {split!r}")
        result = run_coagency_loop(fixture.task, config=FULL_COAGENCY_CONFIG)
        diag = result.diagnostics
        first = diag.first_pass_ranking[0]["description"] if diag.first_pass_ranking else None
        final = diag.final_ranking[0]["description"] if diag.final_ranking else None
        reordered = (first is not None and final is not None and first != final)
        if expect_reordering:
            self.assertTrue(
                reordered,
                f"{task_id}: expected a reordering but first_pass={first!r} == final={final!r}",
            )
        else:
            self.assertFalse(
                reordered,
                f"{task_id}: unexpected reordering: first_pass={first!r} → final={final!r}",
            )

    def test_crop_rotate_reorders(self) -> None:
        """crop_rotate_task should produce a reordering: crop_to_content → crop_to_content->rotate90."""
        self._check_reordering("crop_rotate_task", "regression", expect_reordering=True)

    def test_holdout_crop_flip_reorders(self) -> None:
        """holdout_composition_crop_flip_task must reorder: primitive crop → composed crop+flip."""
        self._check_reordering(
            "holdout_composition_crop_flip_task", "blind_holdout", expect_reordering=True
        )

    def test_holdout_largest_rotate_reorders(self) -> None:
        """holdout_composition_largest_rotate_task must reorder: largest_object → composition."""
        self._check_reordering(
            "holdout_composition_largest_rotate_task", "blind_holdout", expect_reordering=True
        )

    def test_ambiguous_competing_reorders(self) -> None:
        """ambiguous_competing_regression_task must reorder: largest_object → composition."""
        self._check_reordering(
            "ambiguous_competing_regression_task", "regression", expect_reordering=True
        )

    def test_identity_task_no_reordering(self) -> None:
        """identity_task should NOT reorder: a primitive solves it directly."""
        self._check_reordering("identity_task", "dev", expect_reordering=False)


class PrimitiveBaselineDiscriminativenessTests(unittest.TestCase):
    """Verify that the new holdout tasks are not solved by the primitive baseline."""

    def _baseline_solves(self, task_id: str, split: str) -> bool:
        fixtures = load_fixture_split("data/fixtures", split)
        fixture = next((f for f in fixtures if f.task_id == task_id), None)
        if fixture is None:
            return False
        result = run_coagency_loop(fixture.task, config=PRIMITIVE_BASELINE_CONFIG)
        h1, _ = select_top_two(result.ranked_hypotheses, fixture.task.test[0].input)
        if h1 is None:
            return False
        output = apply_hypothesis(h1, fixture.task.test[0].input)
        if output is None or not fixture.expected_outputs:
            return False
        return output.equals(fixture.expected_outputs[0])

    def test_holdout_crop_flip_not_solved_by_baseline(self) -> None:
        self.assertFalse(
            self._baseline_solves("holdout_composition_crop_flip_task", "blind_holdout"),
            "holdout_composition_crop_flip_task should NOT be solved by primitive_baseline_only",
        )

    def test_holdout_largest_rotate_not_solved_by_baseline(self) -> None:
        self.assertFalse(
            self._baseline_solves("holdout_composition_largest_rotate_task", "blind_holdout"),
            "holdout_composition_largest_rotate_task should NOT be solved by primitive_baseline_only",
        )

    def test_holdout_crop_flip_solved_by_full_coagency(self) -> None:
        fixtures = load_fixture_split("data/fixtures", "blind_holdout")
        fixture = next(
            f for f in fixtures if f.task_id == "holdout_composition_crop_flip_task"
        )
        result = run_coagency_loop(fixture.task, config=FULL_COAGENCY_CONFIG)
        h1, _ = select_top_two(result.ranked_hypotheses, fixture.task.test[0].input)
        self.assertIsNotNone(h1, "full_epistemic_coagency must find a hypothesis")
        output = apply_hypothesis(h1, fixture.task.test[0].input)
        self.assertIsNotNone(output)
        self.assertTrue(
            output.equals(fixture.expected_outputs[0]),
            f"Expected {fixture.expected_outputs[0].to_list()} but got {output.to_list()}",
        )

    def test_holdout_largest_rotate_solved_by_full_coagency(self) -> None:
        fixtures = load_fixture_split("data/fixtures", "blind_holdout")
        fixture = next(
            f for f in fixtures if f.task_id == "holdout_composition_largest_rotate_task"
        )
        result = run_coagency_loop(fixture.task, config=FULL_COAGENCY_CONFIG)
        h1, _ = select_top_two(result.ranked_hypotheses, fixture.task.test[0].input)
        self.assertIsNotNone(h1)
        output = apply_hypothesis(h1, fixture.task.test[0].input)
        self.assertIsNotNone(output)
        self.assertTrue(output.equals(fixture.expected_outputs[0]))


class EpistemicReorderingsToolTests(unittest.TestCase):
    """Smoke-test the generate_epistemic_reorderings tool."""

    def test_tool_runs_and_produces_output(self) -> None:
        """Run the tool against actual report data and check key fields exist."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            # Use actual reports directory (read-only) and write to tmp.
            # For a real smoke test we run the analysis against actual reports.
            repo_root = Path(__file__).resolve().parents[1]
            reports_dir = repo_root / "reports"
            if not reports_dir.exists() or not any(reports_dir.iterdir()):
                self.skipTest("No reports directory found; run the benchmark first.")
            result = subprocess.run(
                ["python", "tools/generate_epistemic_reorderings.py", "--reports", str(reports_dir)],
                capture_output=True, text=True, cwd=str(repo_root),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            json_path = reports_dir / "epistemic_reorderings.json"
            self.assertTrue(json_path.exists(), "epistemic_reorderings.json should exist")
            data = json.loads(json_path.read_text())
            # At least one split should have reorderings.
            total_reorderings = sum(
                v.get("tasks_where_first_pass_winner_changed_after_refinement", 0)
                for v in data.values()
            )
            self.assertGreater(total_reorderings, 0, "Should have at least one reordering")


class ThesisValidationSummaryToolTests(unittest.TestCase):
    """Smoke-test the generate_thesis_validation_summary tool."""

    def test_tool_runs_and_answers_all_questions(self) -> None:
        import subprocess
        repo_root = Path(__file__).resolve().parents[1]
        reports_dir = repo_root / "reports"
        if not (reports_dir / "final_split_diagnostics.json").exists():
            self.skipTest("final_split_diagnostics.json not found; run the benchmark first.")
        result = subprocess.run(
            ["python", "tools/generate_thesis_validation_summary.py", "--reports", str(reports_dir)],
            capture_output=True, text=True, cwd=str(repo_root),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        json_path = reports_dir / "thesis_validation_summary.json"
        self.assertTrue(json_path.exists())
        data = json.loads(json_path.read_text())
        for key in [
            "q1_discriminative", "q2_full_beats_baseline", "q3_uncertainty_present",
            "q4_uncertainty_decision_relevant", "q5_reorderings_occur",
            "q6_proven", "q6_suggested", "q6_untestable", "overall_verdict",
        ]:
            self.assertIn(key, data, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main()
