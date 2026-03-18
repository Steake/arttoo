import unittest

from arc_epistemic.eval.analysis import categorize_failure, group_failures
from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.solver.solver import solve_task_with_diagnostics


class FailureTaxonomyTests(unittest.TestCase):
    def test_failure_taxonomy_marks_unsupported_pattern(self) -> None:
        fixture = load_fixture_split("data/fixtures", split="regression")[1]
        result = solve_task_with_diagnostics(fixture.task)
        failure = categorize_failure(fixture, result)
        self.assertEqual(failure.primary_class, "unsupported_pattern")
        self.assertIn("object_count_mismatch", failure.tags)

    def test_group_failures_aggregates_primary_classes(self) -> None:
        payload = [
            {"task_id": "a", "failure_primary_class": "unsupported_pattern", "failure_tags": ["unsupported_pattern"]},
            {"task_id": "b", "failure_primary_class": "unsupported_pattern", "failure_tags": ["unsupported_pattern", "object_count_mismatch"]},
        ]
        summary = group_failures(payload, split="regression")
        self.assertEqual(summary["split"], "regression")
        self.assertEqual(summary["failure_classes"]["unsupported_pattern"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
