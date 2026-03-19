import unittest

from arc_epistemic.eval.analysis import categorize_failure, group_failures
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.solver.solver import solve_task_with_diagnostics


class FailureTaxonomyTests(unittest.TestCase):
    def test_failure_taxonomy_marks_unsupported_pattern(self) -> None:
        fixtures = load_fixture_split("data/fixtures", split="regression")
        fixture = next(f for f in fixtures if f.task_id == "unsupported_pattern_task")
        result = solve_task_with_diagnostics(fixture.task)
        failure = categorize_failure(fixture, result)
        self.assertEqual(failure.primary_class, "unsupported_pattern")
        self.assertIn("object_count_mismatch", failure.tags)

    def test_group_failures_aggregates_primary_classes(self) -> None:
        payload = [
            {"task_id": "a", "failure_primary_class": "unsupported_pattern", "failure_tags": ["unsupported_pattern"], "transform_crash_count": 0, "shape_mismatch_count": 0},
            {"task_id": "b", "failure_primary_class": "unsupported_pattern", "failure_tags": ["unsupported_pattern", "object_count_mismatch"], "transform_crash_count": 0, "shape_mismatch_count": 0},
        ]
        summary = group_failures(payload, split="regression")
        self.assertEqual(summary["split"], "regression")
        self.assertEqual(summary["failure_classes"]["unsupported_pattern"]["count"], 2)
        self.assertEqual(summary["final_task_failure_count"], 2)
        self.assertEqual(summary["unsupported_pattern_exit_count"], 2)
        self.assertEqual(summary["candidate_transform_failure_count"], 0)
        self.assertEqual(summary["shape_mismatch_rejection_count"], 0)


if __name__ == "__main__":
    unittest.main()
