import unittest

import pyiron_xzzx


class TestVersion(unittest.TestCase):
    def test_version(self):
        version = pyiron_xzzx.__version__
        print(version)
        self.assertTrue(version.startswith("0"))
