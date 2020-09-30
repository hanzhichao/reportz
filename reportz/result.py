import inspect
import platform
import sys
import time
import traceback
import unittest
import io
from unittest.result import failfast
import re
import threading
from collections import defaultdict

from logz import log
log.format = '%(asctime)s %(threadName)s %(thread)d %(levelname)s %(message)s'


TAG_PARTTEN = 'tag:(\w+)'
LEVEL_PARTTEN = 'level:(\d+)'


def get_case_tags(case: unittest.TestCase) -> list:
    """从用例方法的docstring中匹配出指定格式的tags"""
    case_tags = None
    case_doc = case._testMethodDoc
    if case_doc and 'tag' in case_doc:
        pattern = re.compile(TAG_PARTTEN)
        case_tags = re.findall(pattern, case_doc)
    return case_tags


def get_case_level(case: unittest.TestCase):
    """从用例方法的docstring中匹配出指定格式的level"""
    case_doc = case._testMethodDoc
    case_level = None  # todo 默认level
    if case_doc:
        pattern = re.compile(LEVEL_PARTTEN)
        levels = re.findall(pattern, case_doc)
        if levels:
            case_level = levels[0]
            try:
                case_level = int(case_level)
            except:
                raise ValueError(f'用例中level设置：{case_level} 应为整数格式')
    return case_level


class TestStatus(object):
    SUCCESS = 'success'
    FAIL = 'fail'
    ERROR = 'error'
    SKIPPED = 'skipped'
    XFAIL = 'xfail'
    XPASS = 'xpass'


def time_to_string(timestamp: float) -> str:
    """时间戳转时间字符串"""
    time_array = time.localtime(timestamp)
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
    return time_str


def get_platform_info():
    """获取执行平台信息"""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "python_version": platform.python_version(),
        # "env": dict(os.environ),  # 可能包含敏感信息
    }


def inspect_code(test):
    test_method = getattr(test.__class__, test._testMethodName)
    try:
        code = inspect.getsource(test_method)
    except Exception as ex:
        log.exception(ex)
        code = ''
    return code


class ThreadStringIO(io.StringIO):
    """按线程存取结果"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = defaultdict(str)  # 按线程号存储

    def write(self, text):
        # log.info('线程输出', text)
        thread_id = str(threading.current_thread().ident)
        super().write(text)
        self.values[thread_id] += text

    def writelines(self, lines):
        super().writelines(lines)
        thread_id = str(threading.current_thread().ident)
        text = ''.join(lines)
        self.values[thread_id] += text

    def getvalues(self):
        """返回线程结果字典"""
        return self.values


class TestCaseResult(object):
    """用例测试结果"""

    def __init__(self, test: unittest.case.TestCase, name=None):
        self.test = test  # 测试用例对象

        self.name = name or test._testMethodName  # 支持传入用例别名，unittest.TestCase自带属性方法
        self.id = test.id()  # 用例完整路径，unittest.TestCase自带方法
        self.description = test.shortDescription()  # 用例简要描述，unittest.TestCase自带方法
        self.doc = test._testMethodDoc  # 用例docstring，，unittest.TestCase自带属性方法
        self.module_name = test.__module__  # 用例所在模块名
        self.class_name = test.__class__.__name__  # 用例所在类名
        self.class_id = f'{test.__module__}.{test.__class__.__name__}'  # 用例所在类完整路径
        self.class_doc = test.__class__.__doc__  # 用例所在类docstring描述

        self.tags = get_case_tags(test)  # 获取用例tags
        self.level = get_case_level(test)  # 获取用例level等级
        self.code = inspect_code(test)  # 获取用例源代码

        # 用例执后更新的信息
        self.start_at = None  # 用例开始时间
        self.end_at = None  # 用例结束时间
        self.duration = None  # 用例执行持续时间

        self.status = None  # 用例测试状态
        self.output = None  # 用例内的print信息
        self.exc_info = None  # 用例异常信息
        self.reason = None  # 跳过,失败,出错原因

    @property
    def data(self):  # 组合字典格式的用例结果数据
        data = dict(
            name=self.name,
            id=self.test.id(),
            description=self.description,
            status=self.status,
            tags=self.tags,
            level=self.level,
            time=dict(
                start_at=self.start_at,
                end_at=self.end_at,
                duration=self.duration
            ),
            class_name=self.class_name,
            class_doc=self.class_doc,
            module_name=self.module_name,
            code=self.code,
            output=self.output,
            exc_info=self.exc_info,
            reason=self.reason,
        )
        return data


class TestResult(unittest.TestResult):
    """测试结果,补充整个过程的运行时间"""

    def __init__(self,
                 stream=None,
                 descriptions=None,
                 verbosity=None,
                 ):

        super().__init__(stream, descriptions, verbosity)
        self.successes = []
        self.testcase_results = []  # 执行的用例结果列表
        self.verbosity = verbosity or 1
        self.buffer = True
        self.know_exceptions = None

        self.name = None
        self.start_at = None
        self.end_at = None
        self.duration = None
        self.successes_count = 0
        self.failures_count = 0
        self.errors_count = 0
        self.skipped_count = 0
        self.expectedFailures_count = 0
        self.unexpectedSuccesses_count = 0

        self._stdout_buffers = dict() # 按线程存
        self._stderr_buffers = dict() # 按线程存
        self.threadId = str(threading.current_thread().ident)


    @property
    def summary(self):
        """组装结果概要, details分按运行顺序和按类组织两种结构"""
        data = dict(
            name=self.name,
            success=self.wasSuccessful(),
            stat=dict(
                testsRun=self.testsRun,
                successes=self.successes_count,
                failures=self.failures_count,
                errors=self.errors_count,
                skipped=self.skipped_count,
                expectedFailures=self.expectedFailures_count,
                unexpectedSuccesses=self.unexpectedSuccesses_count,
            ),
            time=dict(
                start_at=self.start_at,
                end_at=self.end_at,
                duration=self.duration
            ),
            platform=get_platform_info(),  # 环境信息的最后状态
            details=[testcase_result.data for testcase_result in self.testcase_results]
        )
        return data

    def _setupStdout(self):
        """分线程存储"""
        # rlock.acquire()
        # if self._stdout_buffers.get(self.threadId) is None:
        #     self._stdout_buffers[self.threadId] = io.StringIO()
        #     self._stderr_buffers[self.threadId] = io.StringIO()
        #     sys.stdout = self._stdout_buffers[self.threadId]
        #     sys.stderr = self._stderr_buffers[self.threadId]

        if self.buffer:
            if self._stderr_buffer is None:
                # self._stderr_buffer = io.StringIO()
                # self._stdout_buffer = io.StringIO()
                self._stderr_buffer = ThreadStringIO()
                self._stdout_buffer = ThreadStringIO()
            sys.stdout = self._stdout_buffer
            sys.stderr = self._stderr_buffer

    def _restoreStdout(self):
        """重写父类的_restoreStdout方法"""
        if self.buffer:
            # if self._mirrorOutput:
            #     output = sys.stdout.getvalue()
            #     error = sys.stderr.getvalue()
            outputs = self._stdout_buffer.getvalues()
            errors = self._stderr_buffer.getvalues()

            sys.stdout = self._original_stdout
            sys.stdout = self._original_stderr
            self._stdout_buffer.seek(0)
            self._stdout_buffer.truncate()
            self._stderr_buffer.seek(0)
            self._stderr_buffer.truncate()
            return outputs, errors

    def _get_exc_msg(self, err):
        exctype, value, tb = err
        exc_msg = str(value)
        exc_full_path = f'{exctype.__module__}.{exctype.__name__}'
        if self.know_exceptions and isinstance(self.know_exceptions, dict):
            exc_msg = self.know_exceptions.get(exc_full_path, exc_msg)
        return exc_msg

    def _exc_info_to_string(self, err, test):
        """重写父类的转换异常方法, 去掉buffer的输出"""
        exctype, value, tb = err
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next

        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
        else:
            length = None
        tb_e = traceback.TracebackException(
            exctype, value, tb, limit=length, capture_locals=self.tb_locals)
        msgLines = list(tb_e.format())
        return ''.join(msgLines)

    def startTestRun(self):
        """整个执行开始"""
        self.start_at = time.time()
        if self.verbosity > 1:
            log.info(f'===== 测试开始, 开始时间: {time_to_string(self.start_at)} =====')

    def stopTestRun(self):
        """整个执行结束"""
        self.end_at = time.time()
        self.duration = self.end_at - self.start_at
        self.success = self.wasSuccessful()
        if self.verbosity > 1:
            log.info(f'===== 测试结束, 持续时间: {self.duration}秒 =====')

        # log.info(self.summary['stat'])
        # log.info(self.summary['time'])

    def startTest(self, test: unittest.case.TestCase):
        """单个用例执行开始"""
        test.result = TestCaseResult(test)
        self.testcase_results.append(test.result)
        test.result.thread_id = str(threading.current_thread().ident)  # 线程id
        test.result.start_at = time.time()
        self.testsRun += 1
        # self._mirrorOutput = False
        self._setupStdout()

        if self.verbosity > 1:
            log.info(f'执行用例: {test.result.name}: {test.result.description}, 开始时间: {time_to_string(test.result.start_at)}')

    def stopTest(self, test: unittest.case.TestCase) -> None:
        """单个用例结束"""
        test.result.end_at = time.time()
        test.result.duration = test.result.end_at - test.result.start_at

        outputs, errors = self._restoreStdout()
        test_output = outputs.get(test.result.thread_id, '') + errors.get(test.result.thread_id, '')
        test.result.output = test_output.strip()

        if self.verbosity > 1:
            log.info(f'结果: {test.result.status}, 持续时间: {test.result.duration}秒')
        elif self.verbosity > 0:
            log.info(f'{test.result.name} ...  {test.result.status}')

        if self.verbosity > 0:
            if test.result.output:
                log.info(f'{test.result.output.strip()}')

            if test.result.exc_info:
                log.exception(test.result.exc_info)

    def addSuccess(self, test):
        """重写父类方法, 单个用例成功时在stopTest前调用"""
        test.result.status = TestStatus.SUCCESS
        self.successes.append(test)
        self.successes_count += 1
        # super().addSuccess(test)

    @failfast
    def addFailure(self, test, err):
        """重写父类方法, 用例失败时在stopTest前调用"""
        test.result.status = TestStatus.FAIL
        test.result.exc_info = self._exc_info_to_string(err, test)
        test.result.reason = self._get_exc_msg(err)
        self.failures_count += 1
        # super().addFailure(test, err)
        self.failures.append((test, self._exc_info_to_string(err, test)))
        # self._mirrorOutput = True

    @failfast
    def addError(self, test, err):
        """重写父类方法, 用例异常时在stopTest前调用"""
        test.result.status = TestStatus.ERROR
        test.result.exc_info = self._exc_info_to_string(err, test)
        test.result.reason = self._get_exc_msg(err)
        self.errors_count += 1
        # super().addError(test, err)
        self.errors.append((test, self._exc_info_to_string(err, test)))
        # self._mirrorOutput = True

    def addSkip(self, test, reason):
        """重写父类方法, 用例跳过时在stopTest前调用"""
        test.result.status = TestStatus.SKIPPED
        test.result.reason = reason
        self.skipped_count += 1
        # super().addSkip(test, reason)
        self.skipped.append((test, reason))

    def addExpectedFailure(self, test, err):
        """重写父类方法, 用例期望失败时在stopTest前调用"""
        test.result.status = TestStatus.XFAIL
        test.result.exc_info = self._exc_info_to_string(err, test)
        test.result.reason = self._get_exc_msg(err)
        self.expectedFailures_count += 1
        # super().addExpectedFailure(test, err)
        self.expectedFailures.append(
            (test, self._exc_info_to_string(err, test)))

    @failfast
    def addUnexpectedSuccess(self, test):
        """重写父类方法, 用例非期望成功时在stopTest前调用"""
        test.result.status = TestStatus.XPASS
        self.expectedFailures_count += 1
        # super().addUnexpectedSuccess(test)
        self.unexpectedSuccesses.append(test)