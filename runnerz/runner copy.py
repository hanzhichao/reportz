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
import pickle
import time
import signal
import inspect
import importlib
from concurrent.futures import ThreadPoolExecutor

def is_case( case):
    return unittest.suite._isnotsuite(case)

def is_case_failed(case):
    if (getattr(case.__class__, '_classSetupFailed', False) or getattr(result, '_moduleSetUpFailed', False)):
        return True
    return false

class Runner(object):
    def collect_only(self, suite):   # 仅列出所用用例
        t0 = time.time()
        i = 0
        for test in suite:
            if _isnotsuite(test):
                i += 1
                print("{}.{}".format(str(i), case.id()))
        print("----------------------------------------------------------------------")
        print("Collect {} tests is {:.3f}s".format(str(i),time.time()-t0))

    def save_failures(self, result, file):   # file为序列化保存的文件名，配置在config/config.py中
        suite = unittest.TestSuite()
        for case_result in result.failures:   # 组装TestSuite
            suite.addTest(case_result[0])   # case_result是个元祖，第一个元素是用例对象，后面是失败原因等等

        with open(file, 'wb') as f:
            pickle.dump(suite, f)    # 序列化到指定文件

    def rerun_fails(self):  # 失败用例重跑方法
        sys.path.append(test_case_path)   # 需要将用例路径添加到包搜索路径中，不然反序列化TestSuite会找不到用例
        with open(last_fails_file, 'rb') as f:
            suite = pickle.load(f)    # 反序列化得到TestSuite
        run(suite)

    def run_suite_after(self, suite, result):
        suite._tearDownPreviousClass(None, result)
        suite._handleModuleTearDown(result)

    def run_suite_before_case(self, suite, case, result):
        suite._tearDownPreviousClass(test_case, result)
        suite._handleModuleFixture(test_case, result)
        suite._handleClassSetUp(test_case, result)
        result._previousTestClass = test_case.__class__

        if (getattr(test_case.__class__, '_classSetupFailed', False) or
                getattr(result, '_moduleSetUpFailed', False)):
            continue


    def run_suite(self, suite, result, run_func=None, interval=None):
        for case in suite:
            if _isnotsuite(case):
                self.run_suite_before_case(suite, case, result)
                if run_func is None:
                    case(result)
                else:
                    run_func(case, result)
                if interval:
                    time.sleep(interval)
        self.run_suite_after(suite, result)


    def run_suite_in_thread_poll(self, suite, result, thread_num, interval=None):
        poll = ThreadPoolExecutor(max_workers=thread_num)
        self.run_suite(suite, result, 
                       run_func=lambda case, result: poll.submit(case, result), 
                       interval=interval)


    # def run_by_dir(self, path):
    #     suite = discover(path)
    #     self.run(suite)

    # def run_by_dirs(self, paths):
    #     pass

    # def run_by_file(self, file_path):
    #     pass

    # def run_by_class(self, class_path):
    #     pass

    # def run_by_case(self, case_path):
    #     pass

    # def run_by_list(self, case_list):
    #     pass

    # def run_by_suite(self, suite):
    #     pass



class HTMLRunner(Runner):
    def __init__(self, output, title="Test Report", description="", template='simple', **kwargs):
        self.file = datetime.now().strftime(output)
        self.title = title
        self.description = description
        self.template = template
        self.kwargs = kwargs
        self.timeout = 10

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

    def generate_report(self, result, start_at, end_at):
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
                    "duration": end_at - start_at,
                    "platform": platform.platform(),
                    "system": platform.system(),
                    "python_version": platform.python_version(),
                    "env": dict(os.environ),
                }
        context.update(self.kwargs)
        content = Template(template_content).render(context)
        with open(self.file, "w") as f:
            f.write(content)  # 写入文件

    def run(self, suite):
        # start_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_at = datetime.now()
        result = Result()   # 用于保存测试结果
        # suite(result)  # 执行测试
        self.run_suite(suite, result)

        end_at = datetime.now()
        self.generate_report(result, start_at, end_at)
        
        return result


if __name__ == "__main__":

    pass