import time
import os
import unittest
from jinja2 import Template

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# with open('.bootstrap_simple.html')
TPL = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{title}}</title>
    <link rel="stylesheet" href="https://cdn.staticfile.org/twitter-bootstrap/4.1.0/css/bootstrap.min.css">
</head>
<body>
<div class="container">
    <h1 class="pt-4">测试报告</h1>
    <h6>测试报告描述信息</h6>
    <h6>执行: {{run_num}} 通过: {{pass_num}} 失败: {{fail_num}} 出错: {{error_num}} 跳过: {{skipped_num}}</h6>
    <h6 class="pb-2">执行时间: {{duration}}s</h6>
    <table class="table table-striped">
        <thead><tr><th>用例名</th><th>状态</th><th>执行信息</th></tr></thead>
        <tbody>
            {% for case in cases %}
            <tr><td>{{case.name}}</td><td>{{case.status}}</td><td>{{case.exec_info}}</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>

</body>
</html>
'''


class Result(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.success = []
        self.cases = []

    def addSuccess(self, test):
        self.success.append(test)
        self.cases.append({"name": test.id(), "status": "pass", "exec_info": ""})

    def addError(self, test, exec_info):
        self.errors.append((test, exec_info))
        self.cases.append({"name": test.id(), "status": "error",
                           "exec_info": self._exc_info_to_string(exec_info, test)
                          .replace("\n", "<br/>")})

    def addFailure(self, test, exec_info):
        self.failures.append((test, exec_info))
        self.cases.append({"name": test.id(), "status": "fail",
                           "exec_info": self._exc_info_to_string(exec_info, test)
                          .replace("\n", "<br/>")})

    def addSkip(self, test, skip_reason):
        self.skipped.append((test, skip_reason))
        self.cases.append({"name": test.id(), "status": "skip",
                           "exec_info": skip_reason})

    def addExpectedFailure(self, test, exec_info):
        self.success.append(test)
        self.cases.append({"name": test.id(), "status": "pass",
                           "exec_info": self._exc_info_to_string(exec_info, test)
                          .replace("\n", "<br/>")})

    def addUnexpectedSuccess(self, test):
        self.failures.append((test, "UnexpectedSuccess"))
        self.cases.append({"name": test.id(), "status": "fail", "exec_info": "UnexpectedSuccess"})


class HTMLRunner(object):
    def __init__(self, output, title="Test Report", description=""):
        self.file = output
        self.title = title
        self.description = description

    def run(self, suite):
        result = Result()   # 用于保存测试结果
        start_time = time.time()
        suite(result)  # 执行测试
        duration = round(time.time() - start_time, 6)
        print(len(result.success), len(result.failures))
        # 渲染数据到模板
        content = Template(TPL).render({"title": self.title,
                                        "description": self.description,
                                        "cases": result.cases,
                                        "run_num": result.testsRun,
                                        "pass_num": len(result.success),
                                        "fail_num": len(result.failures),
                                        "skipped_num": len(result.skipped),
                                        "error_num": len(result.errors),
                                        "duration": duration})
        with open(self.file, "w") as f:
            f.write(content)  # 写入文件
        return result


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("./")
    HTMLRunner(output="report.html",
               title="测试报告",
               description="测试报告描述").run(suite)