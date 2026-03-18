import unittest

from arc_epistemic.primitives.color import apply_color_map
from arc_epistemic.primitives.objects import extract_objects
from arc_epistemic.primitives.symmetry import flip_horizontal, rotate90
from arc_epistemic.utils.grid import Grid


class PrimitiveTests(unittest.TestCase):
    def test_connected_components_extract_objects(self) -> None:
        grid = Grid.from_list(
            [
                [0, 1, 1, 0],
                [0, 1, 0, 0],
                [2, 0, 0, 2],
            ]
        )
        objects = extract_objects(grid, background=0)
        self.assertEqual(len(objects), 3)
        self.assertEqual(objects[0].color, 1)
        self.assertEqual(objects[0].size, 3)

    def test_rotations_and_flips(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        self.assertEqual(flip_horizontal(grid).to_list(), [[2, 1], [4, 3]])
        self.assertEqual(rotate90(grid).to_list(), [[2, 4], [1, 3]])

    def test_color_map(self) -> None:
        grid = Grid.from_list([[0, 1], [1, 2]])
        remapped = apply_color_map(grid, {1: 3, 2: 4})
        self.assertEqual(remapped.to_list(), [[0, 3], [3, 4]])


if __name__ == "__main__":
    unittest.main()
