import unittest

from arc_epistemic.eval.fixtures import load_fixture_split
from arc_epistemic.solver.solver import solve_task_with_diagnostics


class TelemetryTests(unittest.TestCase):
    def test_solver_emits_rich_telemetry(self) -> None:
        fixture = load_fixture_split("data/fixtures", split="dev")[0]
        result = solve_task_with_diagnostics(fixture.task)
        diagnostics = result.loop_diagnostics
        self.assertTrue(diagnostics.generated_candidates)
        self.assertTrue(diagnostics.first_pass_ranking)
        self.assertTrue(diagnostics.final_ranking)
        self.assertIsInstance(result.run_fingerprint, str)
        self.assertTrue(result.run_fingerprint)


if __name__ == "__main__":
    unittest.main()
