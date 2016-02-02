#!/usr/bin/python
# coding=utf-8

from smartcache.redis_cache import Cache
import unittest
import time


class CacheTest(unittest.TestCase):
    """
    redis 2.88.11
    """
    def setUp(self):
        self.cc = Cache()
        self.key = str(time.time())

    def tearDown(self):
        self.cc.delete(self.key)

    def test_set_get(self):
        self.assertTrue(self.cc.set(self.key, self.key) is None)
        self.assertTrue(self.cc.get(self.key) == self.key)

    def test_redis_command(self):
        with self.assertRaises(AttributeError):
            self.cc.mset

        with self.assertRaises(AttributeError):
            self.cc.aaaa

    def test_pack_unpack(self):
        key1, key2, key3 = self.key, self.key, '%s_%s'%(self.key, self.key)
        self.assertTrue(self.cc.pack(key1, key2)==key3)
        tmp1, tmp2 = self.cc.unpack(key3)
        self.assertTrue(key1==tmp1)
        self.assertTrue(key2==tmp2)

    def test_valid(self):
        self.assertFalse(self.cc.valid(''))
        self.assertFalse(self.cc.valid(None))
        self.assertTrue(self.cc.valid('s'))

    def test_append(self):
        self.cc.append(self.key, self.key)
        self.cc.append(self.key, self.key)
        self.assertEqual(self.cc.get(self.key), '%s%s'%(self.key, self.key))

    def test_exists(self):
        self.cc.set(self.key, 1)
        self.assertTrue(self.cc.exists(self.key))
        self.cc.delete(self.key)
        self.assertFalse(self.cc.exists(self.key))

    def test_expire_persist_ttl(self):
        self.cc.set(self.key, 1)
        self.assertTrue(self.cc.exists(self.key))
        self.cc.expire(self.key, 1)
        time.sleep(2)
        self.assertFalse(self.cc.exists(self.key))

        self.cc.set(self.key, 1)
        self.cc.expire(self.key, 3864)
        self.assertTrue(self.cc.ttl(self.key) > 0)
        self.cc.persist(self.key)
        self.assertTrue(self.cc.ttl(self.key) < 0)

    def test_move(self):
        self.cc.move

    def test_object(self):
        self.cc.object

    def test_rename(self):
        self.cc.rename

    def test_renamenx(self):
        self.cc.renamenx

    def test_size_type(self):
        data = [self.key, self.key]
        length = len(data)
        self.cc.lupdate(self.key, data)
        self.assertEqual(self.cc.size(self.key), length)
        self.cc.delete(self.key)

        self.cc.update_set(self.key, data)
        self.assertEqual(self.cc.size(self.key), 1)
        self.cc.delete(self.key)

        self.cc.update_sortedset(self.key, (1, 10))
        self.assertEqual(self.cc.size(self.key), 1)
        self.cc.delete(self.key)

        self.cc.update_sortedset(self.key, [(1, 10), (2, 10)])
        self.assertEqual(self.cc.size(self.key), 2)
        self.cc.delete(self.key)

        self.cc.rupdate(self.key, data)
        self.assertEqual(self.cc.size(self.key), length)
        self.cc.delete(self.key)

    def test_dict(self):
        self.cc.hash(self.key, self.key, self.key)
        self.assertEqual(self.cc.hash(self.key, self.key), self.key)

        self.assertEqual(self.cc.hash_keys(self.key), [self.key])
        self.assertEqual(self.cc.hash_values(self.key), [self.key])
        for k, v in self.cc.hash_items(self.key):
            self.assertEqual(self.key, k)
            self.assertEqual(self.key, v)

        for k, v in self.cc.hash(self.key).items():
            self.assertEqual(self.key, k)
            self.assertEqual(self.key, v)

    def test_list(self):
        #lupdate
        self.cc.lupdate(self.key, self.key)
        ls = self.cc.list(self.key)
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0], self.key)
        self.cc.delete(self.key)

        #rupdate
        self.cc.rupdate(self.key, self.key)
        ls = self.cc.list(self.key)
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0], self.key)
        self.cc.delete(self.key)

        #rpop
        self.cc.lupdate(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 1)
        v = self.cc.rpop(self.key)
        self.assertEqual(v, self.key)
        self.assertEqual(self.cc.size(self.key), 0)

        #lupdate
        self.cc.lupdate(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 1)
        v = self.cc.lpop(self.key)
        self.assertEqual(v, self.key)
        self.assertEqual(self.cc.size(self.key), 0)

    def test_set(self):
        self.cc.update_set(self.key, self.key)
        #contains
        self.assertTrue(self.cc.contains(self.key, self.key))
        self.assertFalse(self.cc.contains(self.key, 't'))
        #set value
        self.assertEqual(self.cc.members(self.key), [self.key])
        #pop value
        self.assertEqual(self.cc.pop_member(self.key, self.key), 1)
        self.assertFalse(self.cc.contains(self.key, self.key))
        self.assertEqual(self.cc.pop_member(self.key, self.key), 0)

        data = [self.key, self.key + '1']
        self.cc.update_set(self.key, data)
        self.assertEqual(self.cc.size(self.key), 2)
        self.cc.pop_member(self.key, data)
        self.assertEqual(self.cc.size(self.key), 0)

        data = [self.key, self.key + '1', self.key + '2']
        self.cc.update_set(self.key, data)
        self.assertEqual(self.cc.size(self.key), len(data))
        self.assertEqual(set(self.cc.members(self.key, with_all=True)), set(data))
        self.assertEqual(set(self.cc.all(self.key)), set(data))

        # sadd
        self.cc.delete(self.key)
        self.cc.sadd(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 1)
        self.assertEqual(set(self.cc.members(self.key, with_all=True)), set([self.key]))
        self.assertEqual(set(self.cc.all(self.key)), set([self.key]))

    def test_sorted(self):
        # sorted members not with score
        self.cc.update_sortedset(self.key, (self.key, 1))
        v = self.cc.sortedset_members(self.key)
        self.assertEqual(v, [self.key])

        # sorted members with score
        v = self.cc.sortedset_members(self.key, withscores=True)
        self.assertEqual(v, [(self.key, 1)])

        # remove by score
        self.assertEqual(self.cc.size(self.key), 1)
        self.cc.remove_member_with_score(self.key, 0, 2)
        self.assertEqual(self.cc.size(self.key), 0)

        # score
        self.cc.update_sortedset(self.key, (self.key, 1))
        self.assertEqual(self.cc.score(self.key, self.key), 1.0)

        # pop member
        self.assertEqual(self.cc.size(self.key), 1)
        self.cc.pop_member(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 0)

        self.cc.update_sortedset(self.key, [(self.key, 1), (self.key+'1', 2)])
        self.assertEqual(self.cc.size(self.key), 2)
        self.cc.pop_member(self.key, [self.key, self.key+'1'])
        self.assertEqual(self.cc.size(self.key), 0)

        # zadd
        self.cc.delete(self.key)
        self.cc.zadd(self.key, self.key, 1)
        v = self.cc.sortedset_members(self.key)
        self.assertEqual(v, [self.key])
        self.assertEqual(self.cc.score(self.key, self.key), 1.0)

    def test_inc(self):
        self.cc.delete(self.key)
        self.cc.inc(self.key)
        self.assertEqual(self.cc.get(self.key), '1')
        self.cc.inc(self.key)
        self.assertEqual(self.cc.get(self.key), '2')

        #inc dict
        self.cc.delete(self.key)
        self.cc.hinc(self.key, self.key)
        self.assertEqual(self.cc.hash(self.key, self.key), '1')

        #inc set
        self.cc.delete(self.key)
        self.cc.update_sortedset(self.key, (self.key, 1))
        self.cc.inc_score(self.key, self.key, 2)
        v = self.cc.sortedset_members(self.key, withscores=True)
        self.assertEqual(v, [(self.key, 3)])

if __name__ == '__main__':
    unittest.main()
