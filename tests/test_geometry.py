import unittest

from arc_epistemic.primitives.geometry import crop_to_content, translate_to_origin
from arc_epistemic.utils.grid import Grid


class GeometryTests(unittest.TestCase):
    def test_crop_to_content(self) -> None:
        grid = Grid.from_list([[0, 0, 0], [0, 2, 2], [0, 2, 0]])
        self.assertEqual(crop_to_content(grid, background=0).to_list(), [[2, 2], [2, 0]])

    def test_translate_to_origin(self) -> None:
        grid = Grid.from_list([[0, 0, 0], [0, 5, 5], [0, 0, 0]])
        self.assertEqual(translate_to_origin(grid, background=0).to_list(), [[5, 5, 0], [0, 0, 0], [0, 0, 0]])


if __name__ == "__main__":
    unittest.main()
