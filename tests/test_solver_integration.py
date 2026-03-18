import unittest

from arc_epistemic.eval.fixtures import load_fixture_tasks
from arc_epistemic.solver.solver import solve_task_with_diagnostics


class SolverIntegrationTests(unittest.TestCase):
    def test_fixture_tasks_end_to_end(self) -> None:
        fixtures = load_fixture_tasks("data/fixtures")
        for fixture in fixtures:
            with self.subTest(task_id=fixture.task_id):
                result = solve_task_with_diagnostics(fixture.task)
                self.assertTrue(result.predictions)
                attempt_1, attempt_2 = result.predictions[0]
                self.assertIsInstance(attempt_1.to_list(), list)
                self.assertIsInstance(attempt_2.to_list(), list)
                self.assertTrue(result.loop_diagnostics.guardrail_ok)

    def test_solver_does_not_crash_on_unsupported_pattern(self) -> None:
        from arc_epistemic.solver.parser import parse_task

        payload = {
            "train": [
                {"input": [[1, 0, 1], [0, 1, 0], [1, 0, 1]], "output": [[1]]},
                {"input": [[2, 0, 2], [0, 2, 0], [2, 0, 2]], "output": [[2]]},
            ],
            "test": [{"input": [[3, 0, 3], [0, 3, 0], [3, 0, 3]]}],
        }
        task = parse_task("unsupported", payload)
        result = solve_task_with_diagnostics(task)
        self.assertTrue(result.predictions)


if __name__ == "__main__":
    unittest.main()
