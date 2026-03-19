import unittest

from arc_epistemic.solver.submission import format_submission
from arc_epistemic.utils.grid import Grid


class SubmissionTests(unittest.TestCase):
    def test_submission_format(self) -> None:
        payload = format_submission(
            {
                "demo": [
                    (
                        Grid.from_list([[1, 0]]),
                        Grid.from_list([[0, 1]]),
                    )
                ]
            }
        )
        self.assertEqual(payload, {"demo": [{"attempt_1": [[1, 0]], "attempt_2": [[0, 1]]}]})


if __name__ == "__main__":
    unittest.main()
