import unittest

from arc_epistemic.solver.executor import apply_hypothesis
from arc_epistemic.solver.hypotheses import composed_hypothesis, primitive_hypothesis
from arc_epistemic.solver.transforms import compose
from arc_epistemic.primitives.symmetry import identity, rotate90
from arc_epistemic.utils.grid import Grid


class HypothesisTests(unittest.TestCase):
    def test_apply_hypothesis(self) -> None:
        hypothesis = primitive_hypothesis("identity", identity, "symmetry", 0)
        grid = Grid.from_list([[1, 2], [3, 4]])
        self.assertEqual(apply_hypothesis(hypothesis, grid).to_list(), [[1, 2], [3, 4]])

    def test_composed_hypothesis(self) -> None:
        base = primitive_hypothesis("identity", identity, "symmetry", 0)
        composed = composed_hypothesis(
            "identity -> rotate90",
            compose(base.transform, rotate90),
            base,
            "symmetry",
            False,
        )
        self.assertEqual(composed.transform(Grid.from_list([[1, 2], [3, 4]])).to_list(), [[2, 4], [1, 3]])
        self.assertEqual(composed.complexity, 2)


if __name__ == "__main__":
    unittest.main()
