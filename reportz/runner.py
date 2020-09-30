import sys;sys.path.insert(0, '/Users/superhin/项目/reportz')
import unittest
import time
from unittest.suite import _isnotsuite

from concurrent.futures import ThreadPoolExecutor

from reportz.result import TestResult


class TestRunner(unittest.TextTestRunner):
    def __init__(self, stream=None, descriptions=True, verbosity=2,
                 failfast=False, buffer=False, resultclass=TestResult, warnings=None,
                 *, tb_locals=False):
        super().__init__(stream, descriptions, verbosity, failfast, buffer, resultclass, warnings, tb_locals=tb_locals)

        self.thread_count = 2
        self.thread_start_wait = 0

    def _threadPoolExecutorTestCase(self, suite, result):
        """多线程运行"""
        with ThreadPoolExecutor(self.thread_count) as pool:
            for test_case in suite:
                if _isnotsuite(test_case):
                    suite._tearDownPreviousClass(test_case, result)
                    suite._handleModuleFixture(test_case, result)
                    suite._handleClassSetUp(test_case, result)
                    result._previousTestClass = test_case.__class__

                    if (getattr(test_case.__class__, '_classSetupFailed', False) or
                            getattr(result, '_moduleSetUpFailed', False)):
                        continue
                pool.submit(test_case, result)
                time.sleep(self.thread_start_wait)
        suite._tearDownPreviousClass(None, result)
        suite._handleModuleTearDown(result)


    def run(self, test):
        result = self._makeResult()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            # test(result)
            self._threadPoolExecutorTestCase(test, result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()

        return result
from logz import log
print = log.print

if __name__ == '__main__':
    from reportz.test_demo import TestDemo
    from pprint import pprint # 需要pip install pprint

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestDemo)
    runner = TestRunner()  # 使用定制的TestResult类
    # from HTMLReport import TestRunner
    # runner = TestRunner(thread_count=2)
    result = runner.run(suite)
    # pprint(result.summary)
    # from logz import log
    # pprint(result.summary[summary'details'][1]['output'])
    # print(result.summary['time']['duration'])
    # pprint(log.outputs)
