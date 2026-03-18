import unittest

from arc_epistemic.utils.grid import BBox, Grid


class GridTests(unittest.TestCase):
    def test_grid_creation_copy_and_equality(self) -> None:
        grid = Grid.from_list([[1, 2], [3, 4]])
        clone = grid.copy()
        self.assertTrue(grid.equals(clone))
        self.assertEqual(grid.shape, (2, 2))
        self.assertEqual(grid.to_list(), [[1, 2], [3, 4]])

    def test_bbox_crop_and_content_bbox(self) -> None:
        grid = Grid.from_list([[0, 0, 0], [0, 5, 5], [0, 5, 0]])
        bbox = grid.content_bbox(background=0)
        self.assertEqual(bbox, BBox(1, 1, 2, 2))
        self.assertEqual(grid.crop(bbox).to_list(), [[5, 5], [5, 0]])


if __name__ == "__main__":
    unittest.main()
