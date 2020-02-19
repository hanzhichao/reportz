import os
import sys
sys.path.append('/Users/apple/Documents/Projects/Self/Pythonz/runnerz')
import unittest
from runnerz.loader import Loader

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
testpath = os.path.join(basedir, 'tests', 'data')
suite = unittest.defaultTestLoader.discover(testpath)
loader = Loader()



if __name__ == "__main__":
    test_divid_tests_by_class()