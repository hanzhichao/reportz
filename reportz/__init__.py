import time
import platform
from datetime import datetime
import os
import unittest
from jinja2 import Template
from collections import defaultdict
from itertools import groupby

# STATUS = {
#     0: 'pass',
#     1: 'fail',
#     2: 'error',
#     3: 'skipped'
# }


class Result(unittest.TestResult):
    def __init__(self, verbosity=1):
        super().__init__(verbosity=verbosity)
        self.verbosity = verbosity
        self.success = []
        self.results = []
        self.test_class = defaultdict(list)
        self.sn = 1

    def register(self, test, status, exec_info='', log='', imgs=[]):
        # item = (test, status, exec_info)
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
            full_name=test.id(),
            doc=test_method_doc,
            status=status,
            test_class=test_class_name,
            test_class_doc=test_class_doc,
            test_module=test_module_name,
            exec_info=exec_info,
            log=log,
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

    def run(self, suite):
        start_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = Result()   # 用于保存测试结果
        start_time = time.time()
        suite(result)  # 执行测试
        end_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duration = round(time.time() - start_time, 6)
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
                }
        context.update(self.kwargs)
        content = Template(template_content).render(context)
        with open(self.file, "w") as f:
            f.write(content)  # 写入文件
        return result