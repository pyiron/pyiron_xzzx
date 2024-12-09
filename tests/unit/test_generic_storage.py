import unittest

from pyiron_xzzx.generic_storage import HDF5Storage, JSONStorage
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Rectangle:
    upper_left_corner: Point
    lower_right_corner: Point


class TestDataIO(unittest.TestCase):
    def store(self, group):
        group["int"] = 1
        group["float"] = 1.2
        group["string"] = "1"
        rect = Rectangle(Point(1, 2), Point(3, 4))
        group["rect"] = rect

    def check(self, group):
        self.assertEqual(group["int"], 1)
        self.assertAlmostEqual(group["float"], 1.2)
        self.assertEqual(group["string"], "1")
        rect = group["rect"]
        self.assertEqual(rect.upper_left_corner.x, 1)
        self.assertEqual(rect.upper_left_corner.y, 2)
        self.assertEqual(rect.lower_right_corner.x, 3)
        self.assertEqual(rect.lower_right_corner.y, 4)

    def test_json_io(self):
        with JSONStorage("dummy.json", "w") as group:
            self.store(group)
        with JSONStorage("dummy.json", "r") as group:
            self.check(group)

    def test_hdf5_io(self):
        with HDF5Storage("dummy.hdf5", "w") as group:
            self.store(group)
        with HDF5Storage("dummy.hdf5", "r") as group:
            self.check(group)


if __name__ == "__main__":
    unittest.main()
