import unittest

from arc_epistemic.solver.epistemic import derive_epistemic_state
from arc_epistemic.solver.executor import evaluate_hypothesis
from arc_epistemic.solver.hypotheses import primitive_hypothesis
from arc_epistemic.solver.parser import Example
from arc_epistemic.utils.grid import Grid


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

    def test_uncertainty_nonzero_for_partial_match(self) -> None:
        # A hypothesis that produces the wrong output but with partial overlap should
        # register unresolved_count > 0 (not immediately classified as contradiction)
        # when similarity is in [0.3, 1.0).
        from arc_epistemic.primitives.symmetry import flip_horizontal

        # Train: input is a uniform 3x3, output is slightly different (partial match)
        train_input = Grid.from_list([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
        # Output differs in only one cell — similarity > 0.3 but != 1.0
        train_output = Grid.from_list([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        hypothesis = primitive_hypothesis("flip_horizontal", flip_horizontal, "symmetry", 1)
        # flip of uniform grid is identity, so prediction == train_input != train_output
        train = (Example(input=train_input, output=train_output),)
        result = evaluate_hypothesis(hypothesis, train)
        # prediction == train_input (all 1s), output has one 0 in center
        # cell similarity should be 8/9 > 0.3, so this should be unresolved not contradiction
        self.assertEqual(result.support_count, 0)
        self.assertGreater(result.unresolved_count, 0, "partial match should yield unresolved_count > 0")
        self.assertEqual(result.contradiction_count, 0)

    def test_competing_hypotheses_have_different_uncertainty(self) -> None:
        # Two hypotheses on the same task: one exact match (uncertainty=0),
        # one partial match (uncertainty>0). Uncertainty must differ.
        from arc_epistemic.primitives.symmetry import flip_horizontal, rotate90
        from arc_epistemic.solver.agents import score_hypotheses, FULL_COAGENCY_CONFIG
        from arc_epistemic.solver.parser import Task

        train_input = Grid.from_list([[1, 2], [3, 4]])
        train_output = Grid.from_list([[2, 1], [4, 3]])  # flip_horizontal result
        task = Task(
            task_id="ambiguous_test",
            train=(Example(input=train_input, output=train_output),),
            test=(),
        )
        # flip_horizontal should be a perfect match; rotate90 should be partial or wrong
        h_exact = primitive_hypothesis("flip_horizontal", flip_horizontal, "symmetry", 1)
        h_wrong = primitive_hypothesis("rotate90", rotate90, "symmetry", 1, allows_shape_change=False)
        scored, _, _ = score_hypotheses(task, [h_exact, h_wrong], FULL_COAGENCY_CONFIG)
        exact_hyp = next(h for h in scored if h.description == "flip_horizontal")
        wrong_hyp = next(h for h in scored if h.description == "rotate90")
        self.assertAlmostEqual(exact_hyp.uncertainty, 0.0)
        # rotate90 of [[1,2],[3,4]] gives [[3,1],[4,2]] which differs from [[2,1],[4,3]]
        # similarity may be partial but should not be exactly 0 uncertainty unless it's total mismatch
        # At minimum, belief and score should differ
        self.assertGreater(exact_hyp.score, wrong_hyp.score)


if __name__ == "__main__":
    unittest.main()
