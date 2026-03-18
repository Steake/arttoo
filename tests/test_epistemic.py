import unittest

from arc_epistemic.solver.epistemic import derive_epistemic_state


class EpistemicTests(unittest.TestCase):
    def test_epistemic_update(self) -> None:
        belief, disbelief, uncertainty, score = derive_epistemic_state(
            total_pairs=4,
            support_count=2,
            contradiction_count=1,
            unresolved_count=1,
            partial_credit=0.75,
        )
        self.assertAlmostEqual(belief, 0.5)
        self.assertAlmostEqual(disbelief, 0.25)
        self.assertAlmostEqual(uncertainty, 0.25)
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()
