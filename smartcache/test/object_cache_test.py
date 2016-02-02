#-*- coding:utf-8 -*-

import os
import sys
import unittest
import random
import time
import threading

from smartcache.object_cache import Cache

THREAD_COUNT = 0

def object_cache_target(key, value):
    return Cache.get(key) == value

def trace_object_cache_run(func, key, value):
    global THREAD_COUNT
    if func(key, value):
        THREAD_COUNT += 1

class ObjectCacheTest(unittest.TestCase):

    def setUp(self):
        self.oc = Cache()
        self.key = str(time.time())

    def tearDown(self):
        del self.oc

    def test_get_set(self):
        self.oc.set(self.key, self.key)
        self.assertEqual(self.oc.get(self.key), self.key)

    def test_expire(self):
        '''
        create object cache, wait until the value is expired
        make sure the new value is different to old value
        '''
        expire = 5
        start = time.time()
        self.oc.set(self.key, self.key, expire=expire)
        old_value = self.oc.get(self.key)
        while time.time() - start < expire :
            self.assertEqual(self.oc.get(self.key), old_value)
            time.sleep(1)
        self.assertEqual(self.oc.get(self.key), None)

    def test_multi_thread(self):
        self.oc.set(self.key, self.key)
        value = self.oc.get(self.key)
        threads_number = 3
        thread_list = []
        for i in range(threads_number):
            i = threading.Thread(target=trace_object_cache_run, args=(object_cache_target, self.key, value))
            thread_list.append(i)
            i.start()

        for i in thread_list:
            i.join()

        self.assertEqual(threads_number, THREAD_COUNT)

if __name__ == '__main__':
    unittest.main()
