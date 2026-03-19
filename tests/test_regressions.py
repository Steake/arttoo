import unittest

from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.solver.solver import solve_task_with_diagnostics


class RegressionTests(unittest.TestCase):
    def test_golden_outputs_and_rankings(self) -> None:
        fixtures = load_fixture_split("data/fixtures", split="regression")
        for fixture in fixtures:
            with self.subTest(task_id=fixture.task_id):
                result = solve_task_with_diagnostics(fixture.task)
                if fixture.expect_exact:
                    attempt_1, _ = result.predictions[0]
                    self.assertEqual(attempt_1.to_list(), fixture.expected_outputs[0].to_list())
                    observed = [hypothesis.description for hypothesis in result.ranked_hypotheses[: len(fixture.ranking_prefix)]]
                    self.assertEqual(observed, list(fixture.ranking_prefix))


if __name__ == "__main__":
    unittest.main()
