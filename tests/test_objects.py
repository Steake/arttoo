import unittest

from arc_epistemic.primitives.objects import extract_objects
from arc_epistemic.primitives.topology import connected_components
from arc_epistemic.utils.grid import BBox, Grid


class ObjectTests(unittest.TestCase):
    def test_connected_components_4_connectivity(self) -> None:
        mask = [[True, True, False], [False, True, False], [True, False, True]]
        components = connected_components(mask, connectivity=4)
        self.assertEqual(len(components), 3)

    def test_extract_objects_bbox(self) -> None:
        grid = Grid.from_list([[0, 1, 1], [0, 1, 0], [2, 0, 2]])
        objects = extract_objects(grid, background=0)
        self.assertEqual(objects[0].bbox, BBox(0, 1, 1, 2))
        self.assertEqual(objects[0].size, 3)


if __name__ == "__main__":
    unittest.main()
