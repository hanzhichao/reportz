def collect(suite):  
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


# 自定义超时异常
class TimeoutError(Exception):
    def __init__(self, msg):
        super(TimeoutError, self).__init__()
        self.msg = msg


def timeout(interval, callback):
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


def do_dot(nodes):
    cur = __import__(nodes[0])
    for node in nodes[1:]:
        cur = getattr(cur, node)
    return cur

