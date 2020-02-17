import sys
sys.path.append('/Users/apple/Documents/Projects/Self/Pythonz/reportz')
import unittest
from reportz import HTMLRunner
import logging


class TestReportz(unittest.TestCase):
    def test_success(self):
        print('success')

    def test_fail(self):
        logging.info('fail')
        assert 0

    def test_error(self):
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')


if __name__ == "__main__":
    # suite = unittest.defaultTestLoader.discover("./")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReportz)
    HTMLRunner(output="report.html",
               title="测试报告",
               description="测试报告描述").run(suite)