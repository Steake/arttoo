import unittest

from arc_epistemic.primitives.symmetry import flip_horizontal, rotate90
from arc_epistemic.solver.hypotheses import primitive_hypothesis
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.utils.grid import Grid


class SelectionTests(unittest.TestCase):
    def test_select_top_two_returns_distinct_predictions(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        first = primitive_hypothesis("rotate90", rotate90, "symmetry", 1)
        second = primitive_hypothesis("flip_horizontal", flip_horizontal, "symmetry", 1)
        top_1, top_2 = select_top_two([first, second], grid)
        self.assertEqual(top_1.description, "rotate90")
        self.assertEqual(top_2.description, "flip_horizontal")


if __name__ == "__main__":
    unittest.main()
