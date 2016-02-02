#-*- coding:utf-8 -*-
from __future__ import absolute_import, division, print_function, with_statement

from smartcache.test.util import unittest

TEST_MODULES = [
    'redis_cache_test',
    'object_cache_test',
]


def main():
    testSuite = unittest.TestSuite()
    for module in TEST_MODULES:
        suite = unittest.TestLoader().loadTestsFromName(module)
        testSuite.addTest(suite)

    result = unittest.TestResult()
    testSuite.run(result)
    for k, v in result.errors:
        print(k)
        print(v)

    for k, v in result.failures:
        print(k)
        print(v)

if __name__ == '__main__':
    main()
