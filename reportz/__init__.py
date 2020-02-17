import time
import platform
from datetime import datetime
import os
import unittest
from jinja2 import Template
from collections import defaultdict
from itertools import groupby
import sys
import io
from unittest.suite import _isnotsuite

import time
import signal


# 自定义超时异常
class TimeoutError(Exception):
    def __init__(self, msg):
        super(TimeoutError, self).__init__()
        self.msg = msg


def time_out(interval, callback):
    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("run func timeout")

        def wrapper(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(interval)       # interval秒后向进程发送SIGALRM信号
                result = func(*args, **kwargs)
                signal.alarm(0)              # 函数在规定时间执行完后关闭alarm闹钟
                return result
            except TimeoutError as e:
                callback(func, e)
        return wrapper
    return decorator


def timeout_callback(e):
    print(e.msg)

# STATUS = {
#     0: 'pass',
#     1: 'fail',
#     2: 'error',
#     3: 'skipped'
# }


class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


class Result(unittest.TestResult):
    def __init__(self, verbosity=1):
        super().__init__(verbosity=verbosity)
        self.verbosity = verbosity
        
        self.success = []
        self.timeouts = []
        self.results = []
        self.test_class = defaultdict(list)
        self.sn = 1
        self.stdout_bak = None
        self.stderr_bak = None
    
    def startTest(self, test):
        self.test_case_start_at = datetime.now()
        super().startTest(test)
        # 重定向sys.out和sys.err
        self.output = io.StringIO()
        stdout_redirector.fp = self.output
        stderr_redirector.fp = self.output
        self.stdout_bak = sys.stdout
        self.stderr_bak = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        if self.stdout_bak:
            sys.stdout = self.stdout_bak
            sys.stderr = self.stderr_bak
            self.stdout_bak = None
            self.stderr_bak = None
        return self.output.getvalue()

    def stopTest(self, test):
        self.complete_output()


    def register(self, test, status, exec_info='', log='', imgs=[]):
        # item = (test, status, exec_info)
        self.test_case_end_at = datetime.now()
        self.test_case_duration = self.test_case_end_at - self.test_case_start_at

        output = self.complete_output()
        sys.stdout.write(output)

        test_module_name = test.__module__
        test_class_name = test.__class__.__name__
        test_class_doc = test.__class__.__doc__
        test_method_name = test._testMethodName
        test_method_doc = test._testMethodDoc

        if test_module_name == '__main__':
            test_module_name = ''
        else:
            test_class_name = '%s.%s' % (test_module_name, test_class_name)

        item = dict(test=test, 
            sn = self.sn,
            name=test_method_name,
            start_at=self.test_case_start_at,
            end_at=self.test_case_end_at,
            duration=self.test_case_duration,
            full_name=test.id(),
            doc=test_method_doc,
            status=status,
            test_class=test_class_name,
            test_class_doc=test_class_doc,
            test_module=test_module_name,
            exec_info=exec_info,
            output=output,
            imgs=imgs,
            )
        self.results.append(item)
        self.sn += 1
        
    def sortByClass(self):
        sorted_results = sorted(self.results, key=lambda x: x['test_class'])
        data = defaultdict(dict)
        for name, group in groupby(sorted_results, key=lambda x: x['test_class']):
            test_cases = list(group)
            data[name] = dict(
                name=name,
                test_cases=test_cases,
                total=len(test_cases),
                pass_num=len(list(filter(lambda x: x['status']=="PASS", test_cases))),
                error_num=len(list(filter(lambda x: x['status']=="ERROR", test_cases))),
                fail_num=len(list(filter(lambda x: x['status']=="FAIL", test_cases))),
                skipped_num=len(list(filter(lambda x: x['status']=="SKIPPED", test_cases))),
                xfail_num=len(list(filter(lambda x: x['status']=="XFAIL", test_cases))),
                xpass_num=len(list(filter(lambda x: x['status']=="XPASS", test_cases)))
            )
            test_classes = list(data.values())
        return test_classes

    def addTimeout(self, err, test):
        print('---'*20)
        self.timeouts.append(test)
        raise err

    def addError(self, test, err):
        super().addError(test, err)
        self.register(test, 'ERROR', self._exc_info_to_string(err, test))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.register(test, 'FAIL', self._exc_info_to_string(err, test))

    def addSuccess(self, test):
        self.success.append(test)
        self.register(test, 'PASS')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.register(test, 'SKIPPED', reason)


    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.register(test, 'XFAIL', self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.register(test, 'XPASS', 'UnexpectedSuccess')
        


class HTMLRunner(object):
    def __init__(self, output, title="Test Report", description="", template='simple', **kwargs):
        self.file = datetime.now().strftime(output)
        self.title = title
        self.description = description
        self.template = template
        self.kwargs = kwargs
        self.timeout = 1

    def run_with_timeout(self, test, result, timeout):
        time_out(timeout, result.addTimeout)(test)(result)

    def run_suite(self, suite, result, debug=False):
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for index, test in enumerate(suite):
            if result.shouldStop:
                break

            if _isnotsuite(test):
                suite._tearDownPreviousClass(test, result)
                suite._handleModuleFixture(test, result)
                suite._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                if (getattr(test.__class__, '_classSetupFailed', False) or
                    getattr(result, '_moduleSetUpFailed', False)):
                    continue

            if not debug:
                if self.timeout:
                    self.run_with_timeout(test, result, self.timeout)
                else:
                    test(result)
            else:
                test.debug()

            if suite._cleanup:
                suite._removeTestAtIndex(index)

        if topLevel:
            suite._tearDownPreviousClass(None, result)
            suite._handleModuleTearDown(result)
            result._testRunEntered = False
        return result


    def run(self, suite):
        # start_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_at = datetime.now()
        result = Result()   # 用于保存测试结果
        start_time = time.time()
        # suite(result)  # 执行测试
        self.run_suite(suite, result)

        end_at = datetime.now()
        duration = end_at - start_at
        # 渲染数据到模板
        basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(basedir, 'templates', '%s.html' % self.template)

        with open(template_path) as f:
            template_content = f.read()
        
        test_classess = result.sortByClass()
        
        context = { "title": self.title,
                    "description": self.description,
                    "test_cases": result.results,
                    "test_classes": test_classess,
                    "total": len(result.results),
                    "run_num": result.testsRun,
                    "pass_num": len(result.success),
                    "fail_num": len(result.failures),
                    "skipped_num": len(result.skipped),
                    "error_num": len(result.errors),
                    "xfail_num": len(result.expectedFailures),
                    "xpass_num": len(result.unexpectedSuccesses),
                    "rerun_num": 0,
                    "start_at": start_at,
                    "end_at": end_at,
                    "duration": duration,
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "python_version": platform.python_version(),
                    "env": dict(os.environ),
                }
        context.update(self.kwargs)
        content = Template(template_content).render(context)
        with open(self.file, "w") as f:
            f.write(content)  # 写入文件
        return result


if __name__ == "__main__":

    # @time_out(2, timeout_callback)
    def task1():
        print("task1 start")
        time.sleep(3)
        print("task1 end")

    # def handler(signum, frame):
    #     raise TimeoutError("run func timeout")

    # signal.signal(signal.SIGALRM, handler)
    # signal.alarm(2)       # interval秒后向进程发送SIGALRM信号
    # task1()
    # signal.alarm(0)
    time_out(task1, 2, timeout_callback)