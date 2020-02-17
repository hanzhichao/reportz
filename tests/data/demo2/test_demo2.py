import unittest
import logging
import time

class TestDemo2(unittest.TestCase):
    def test_success(self):
        print('success')

    def test_timeout(self):
        print('timeout')
        time.sleep(3)

    def test_fail(self):
        logging.info('fail')
        assert 0

    def test_error(self):
        logging.error('error')
        open('abc.txt')

    @unittest.skipIf(True, '原因')
    def test_skip(self):
        print('skip')