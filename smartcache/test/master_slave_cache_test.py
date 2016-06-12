#!/usr/bin/python
# coding=utf-8

from smartcache.redis_cache import MasterSlaveCache
import unittest
import time
import pickle


servers = [
    {'name': 'server1', 'host': '127.0.0.1', 'port': 6379, 'db': 0, 'master': 1},
    {'name': 'server2', 'host': '127.0.0.1', 'port': 6379, 'db': 0,},
    {'name': 'server3', 'host': '127.0.0.1', 'port': 6379, 'db': 0,},
    {'name': 'server4', 'host': '127.0.0.1', 'port': 6379, 'db': 0,},
]

class CacheTest(unittest.TestCase):
    """
    redis 2.88.11
    """
    def setUp(self):
        self.cc = MasterSlaveCache(servers)
        self.keys = [str(time.time()) for i in range(1000)]

    def tearDown(self):
        for k in self.keys:
            self.cc.delete(k)

    def test_shard_cache(self):
        for k in self.keys:
            self.cc.set(k, k)

        for k in self.keys:
            v = self.cc.master_slave_client.get_slave(k).get(k)
            self.assertEqual(pickle.loads(v), k)
        
if __name__ == '__main__':
    unittest.main()