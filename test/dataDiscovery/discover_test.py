import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('../../python'))

from dataDiscovery import discover


class DiscoverTest(unittest.TestCase):

    def test_discover(self):
        pass


if __name__ == '__main__':
    unittest.main()
