import unittest

from arc_epistemic.primitives.symmetry import flip_horizontal, rotate90
from arc_epistemic.solver.hypotheses import primitive_hypothesis
from arc_epistemic.solver.selection import select_top_two
from arc_epistemic.utils.grid import Grid


def _crashing_transform(grid: Grid) -> Grid:
    raise RuntimeError("intentional crash")


class SelectionTests(unittest.TestCase):
    def test_select_top_two_returns_distinct_predictions(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        first = primitive_hypothesis("rotate90", rotate90, "symmetry", 1)
        second = primitive_hypothesis("flip_horizontal", flip_horizontal, "symmetry", 1)
        top_1, top_2 = select_top_two([first, second], grid)
        self.assertEqual(top_1.description, "rotate90")
        self.assertEqual(top_2.description, "flip_horizontal")

    def test_select_skips_failing_top_hypothesis(self) -> None:
        # If the top-ranked hypothesis crashes, the next valid one should become first.
        grid = Grid.from_list([[1, 2], [3, 4]])
        failing = primitive_hypothesis("crashing", _crashing_transform, "symmetry", 1)
        valid = primitive_hypothesis("flip_horizontal", flip_horizontal, "symmetry", 1)
        top_1, top_2 = select_top_two([failing, valid], grid)
        self.assertIsNotNone(top_1)
        self.assertEqual(top_1.description, "flip_horizontal")
        self.assertIsNone(top_2)

    def test_select_top_two_empty_returns_none_none(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        top_1, top_2 = select_top_two([], grid)
        self.assertIsNone(top_1)
        self.assertIsNone(top_2)

    def test_select_top_two_all_failing_returns_none_none(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        failing1 = primitive_hypothesis("crash1", _crashing_transform, "symmetry", 1)
        failing2 = primitive_hypothesis("crash2", _crashing_transform, "symmetry", 1)
        top_1, top_2 = select_top_two([failing1, failing2], grid)
        self.assertIsNone(top_1)
        self.assertIsNone(top_2)
