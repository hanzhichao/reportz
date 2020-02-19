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




        
class Runner(object):
    def collect(self, suite):   # 由于使用discover() 组装的TestSuite是按文件夹目录多级嵌套的，我们把所有用例取出，放到一个无嵌套的TestSuite中，方便之后操作
        new_suite = unittest.TestSuite()

        def _collect(test):   # 递归，如果下级元素还是TestSuite则继续往下找
            if isinstance(test, unittest.TestSuite):
                if test.countTestCases() != 0:
                    for i in test:
                        _collect(i)
            else:
                new_suite.addTest(test)  # 如果下级元素是TestCase，则添加到TestSuite中

        _collect(suite)
        return new_suite

    def discover(self, testspath='.', pattern="*.py"):
        return unittest.defaultTestLoader.discover(testspath, pattern)

    def run_all():
        suite = discover()
        self.run(suite)

    def collect_only(self, suite):   # 仅列出所用用例
        t0 = time.time()
        i = 0
        for case in self.collect():
            i += 1
            print("{}.{}".format(str(i), case.id()))
        print("----------------------------------------------------------------------")
        print("Collect {} tests is {:.3f}s".format(str(i),time.time()-t0))
    
    def makesuite_by_testlist(self, testlist_file):  # test_list_file配置在config/config.py中
        with open(testlist_file) as f:
            testlist = f.readlines()

        testlist = [i.strip() for i in testlist if not i.startswith("#")]   # 去掉每行结尾的"/n"和 #号开头的行

        suite = unittest.TestSuite() 
        all_cases = collect()  # 所有用例
        for case in all_cases:  # 从所有用例中匹配用例方法名
            if case._testMethodName in testlist:
                suite.addTest(case)
        return suite

    def makesuite_by_tag(self, tag):
        suite = unittest.TestSuite()
        for case in collect():
            if case._testMethodDoc and tag in case._testMethodDoc:  # 如果用例方法存在docstring,并且docstring中包含本标签
                suite.addTest(case)
        return suite

    def save_failures(result, file):   # file为序列化保存的文件名，配置在config/config.py中
        suite = unittest.TestSuite()
        for case_result in result.failures:   # 组装TestSuite
            suite.addTest(case_result[0])   # case_result是个元祖，第一个元素是用例对象，后面是失败原因等等

        with open(file, 'wb') as f:
            pickle.dump(suite, f)    # 序列化到指定文件

    def rerun_fails():  # 失败用例重跑方法
        sys.path.append(test_case_path)   # 需要将用例路径添加到包搜索路径中，不然反序列化TestSuite会找不到用例
        with open(last_fails_file, 'rb') as f:
            suite = pickle.load(f)    # 反序列化得到TestSuite
        run(suite)

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