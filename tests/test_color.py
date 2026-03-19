import unittest

from arc_epistemic.primitives.color import apply_color_map, infer_color_mapping
from arc_epistemic.utils.grid import Grid


class ColorTests(unittest.TestCase):
    def test_apply_color_map(self) -> None:
        grid = Grid.from_list([[0, 1], [2, 1]])
        self.assertEqual(apply_color_map(grid, {1: 3, 2: 4}).to_list(), [[0, 3], [4, 3]])

    def test_infer_color_mapping(self) -> None:
        mapping = infer_color_mapping(
            [Grid.from_list([[1, 0], [2, 1]])],
            [Grid.from_list([[3, 0], [4, 3]])],
        )
        self.assertEqual(mapping, {1: 3, 0: 0, 2: 4})


if __name__ == "__main__":
    unittest.main()
