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

    return testSuite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(main())
