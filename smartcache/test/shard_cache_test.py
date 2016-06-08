#!/usr/bin/python
# coding=utf-8

from smartcache.redis_cache import ShardCache
import unittest
import time
import pickle


servers = [
    {'name': 'server1', 'host': '127.0.0.1', 'port': 6379, 'db': 0, 'weight': 1},
    {'name': 'server2', 'host': '127.0.0.1', 'port': 6379, 'db': 1, 'weight': 1},
    {'name': 'server3', 'host': '127.0.0.1', 'port': 6379, 'db': 2, 'weight': 1},
    {'name': 'server4', 'host': '127.0.0.1', 'port': 6379, 'db': 3, 'weight': 1},
]

class CacheTest(unittest.TestCase):
    """
    redis 2.88.11
    """
    def setUp(self):
        self.cc = ShardCache(servers)
        self.keys = [str(time.time()) for i in range(1000)]

    def tearDown(self):
        for k in self.keys:
            self.cc.delete(k)

    def test_shard_cache(self):
        for k in self.keys:
            self.cc.set(k, k)

        for k in self.keys:
            name, host, port, db = tuple(self.cc.shard_client.get_server(k).split(':'))
            conn = self.cc.shard_client.connect_redis(host, int(port), int(db))
            self.assertEqual(pickle.loads(conn.get(k)), k)

if __name__ == '__main__':
    unittest.main()