import unittest
from collections import defaultdict
from unittest.suite import _isnotsuite

loader = unittest.defaultTestLoader

class Loader(unittest.TestLoader):

    # def discover(self, testspath='.', pattern="*.py"):
    #     return unittest.defaultTestLoader.discover(testspath, pattern)

    
    def load_tests_by_config(self, testlist_file):  # test_list_file配置在config/config.py中
        with open(testlist_file) as f:
            testlist = f.readlines()

        testlist = [i.strip() for i in testlist if not i.startswith("#")]   # 去掉每行结尾的"/n"和 #号开头的行

        suite = unittest.TestSuite() 
        all_cases = collect()  # 所有用例
        for case in all_cases:  # 从所有用例中匹配用例方法名
            if case._testMethodName in testlist:
                suite.addTest(case)
        return suite

    def load_tests_by_tag(self, expr):
        suite = unittest.TestSuite()
        for case in collect():
            if case._testMethodDoc and tag in case._testMethodDoc:  # 如果用例方法存在docstring,并且docstring中包含本标签
                suite.addTest(case)
        return suite

    
    def load_tests_by_level(self, expr):
        pass

    def load_last_fails(self):
        pass
