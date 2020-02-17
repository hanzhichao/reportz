import os
import sys
sys.path.append('/Users/apple/Documents/Projects/Self/Pythonz/reportz')
import unittest
from reportz import HTMLRunner
import logging

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
testpath = os.path.join(basedir, 'tests', 'data')
suite = unittest.defaultTestLoader.discover(testpath)


def test_with_default_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc').run(suite)

def test_with_htmltestreportcn_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report_httptestreportcn.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc',template='htmltestreportcn').run(suite)


def test_with_pytest_html_template():
    suite = unittest.defaultTestLoader.discover(testpath)
    HTMLRunner(output="report_pytest_html.html",
               title="测试报告",
               description="测试报告描述", tester='Hzc',template='pytest_html').run(suite)


if __name__ == "__main__":
    # test_with_default_template()
    # test_with_htmltestreportcn_template()
    test_with_pytest_html_template()

    # from HTMLTestReportCN import HTMLTestRunner
    
    # # from HTMLTestRunner_PY3 import HTMLTestRunner
    # with open('report_htmlreport.html', 'wb') as f:  # 从配置文件中读取
    #     HTMLTestRunner(stream=f, title="Api Test", description="测试描述").run(suite)

    # from HTMLReport import TestRunner
    # test_runner = TestRunner(
    #     report_file_name='report_htmlreport',
    #     output_path='.',
    #     title='一个简单的测试报告',
    #     description='随意描述',
    #     thread_count=10,
    #     thread_start_wait=0,
    #     tries=5,
    #     delay=1,
    #     back_off=2,
    #     retry=False,
    #     sequential_execution=True,
    #     lang='cn'
    # )
    # test_runner.run(suite)

    # from pyunitreport import HTMLTestRunner
    # # with open('report_pyunitreport.html', 'wb') as f:  # 从配置文件中读取
    # HTMLTestRunner(output='refer',report_name='pyunitreport.html', report_title="Api Test").run(suite)

    # from HtmlTestRunner import HTMLTestRunner
    # HTMLTestRunner(output='reports').run(suite)

    # from HTMLTestRunner_PY3