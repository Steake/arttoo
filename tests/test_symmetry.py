import unittest

from arc_epistemic.primitives.symmetry import flip_horizontal, flip_vertical, identity, rotate180, rotate270, rotate90
from arc_epistemic.utils.grid import Grid


class SymmetryTests(unittest.TestCase):
    def test_identity_and_reflections(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        self.assertEqual(identity(grid).to_list(), [[1, 2], [3, 4]])
        self.assertEqual(flip_horizontal(grid).to_list(), [[2, 1], [4, 3]])
        self.assertEqual(flip_vertical(grid).to_list(), [[3, 4], [1, 2]])

    def test_rotations(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        self.assertEqual(rotate90(grid).to_list(), [[2, 4], [1, 3]])
        self.assertEqual(rotate180(grid).to_list(), [[4, 3], [2, 1]])
        self.assertEqual(rotate270(grid).to_list(), [[3, 1], [4, 2]])


if __name__ == "__main__":
    unittest.main()
