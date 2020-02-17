import unittest
import logging


class TestDemo1(unittest.TestCase):
    def test_success(self):
        print('success')

    def test_fail(self):
        logging.info('fail')
        print('fail')
        assert 0

    def test_error(self):
        print('error')
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')