import json
import tempfile
import unittest
from pathlib import Path

from arc_epistemic.solver.parser import load_tasks
from arc_epistemic.solver.solver import solve_task
from arc_epistemic.solver.submission import format_submission


class SolverSmokeTests(unittest.TestCase):
    def test_solver_end_to_end_on_rotation_task(self) -> None:
        payload = {
            "demo_task": {
                "train": [
                    {
                        "input": [[1, 2], [3, 4]],
                        "output": [[2, 4], [1, 3]],
                    },
                    {
                        "input": [[5, 6], [7, 8]],
                        "output": [[6, 8], [5, 7]],
                    },
                ],
                "test": [{"input": [[9, 1], [2, 3]]}],
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tasks.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            task = load_tasks(path)["demo_task"]
            predictions = solve_task(task)
        self.assertEqual(predictions[0][0].to_list(), [[1, 3], [9, 2]])
        submission = format_submission({"demo_task": predictions})
        self.assertEqual(submission["demo_task"][0]["attempt_1"], [[1, 3], [9, 2]])
        self.assertIn("attempt_2", submission["demo_task"][0])


if __name__ == "__main__":
    unittest.main()
