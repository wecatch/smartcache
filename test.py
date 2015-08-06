#!/usr/bin/python
# coding=utf-8

from cache import Cache
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
            self.cc.hset

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
        self.cc.lupdate_list(self.key, self.key)
        self.assertTrue(self.cc.size(self.key) == 1)
        self.cc.delete(self.key)

        self.cc.update_set(self.key, 1)
        self.assertTrue(self.cc.size(self.key) == 1)
        self.cc.delete(self.key)

        self.cc.update_sorted_set(self.key, (1, 10))
        self.assertTrue(self.cc.size(self.key) == 1)
        self.cc.delete(self.key)

        self.cc.update_sorted_set(self.key, [(1, 10), (2, 10)])
        self.assertTrue(self.cc.size(self.key) == 2)
        self.cc.delete(self.key)

        self.cc.rupdate_list(self.key, 1)
        self.assertTrue(self.cc.size(self.key) == 1)
        self.cc.delete(self.key)

    def test_dict(self):
        self.cc.update_dict(self.key, self.key, self.key)
        self.assertEqual(self.cc.dict_value(self.key, self.key), self.key)

    def test_list(self):
        self.cc.lupdate_list(self.key, self.key)
        ls = self.cc.list_value(self.key)
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0], self.key)
        self.cc.delete(self.key)

        self.cc.rupdate_list(self.key, self.key)
        ls = self.cc.list_value(self.key)
        self.assertEqual(len(ls), 1)
        self.assertEqual(ls[0], self.key)
        self.cc.delete(self.key)

        self.cc.lupdate_list(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 1)
        v = self.cc.rpop_value(self.key)
        self.assertEqual(v, self.key)
        self.assertEqual(self.cc.size(self.key), 0)

        self.cc.lupdate_list(self.key, self.key)
        self.assertEqual(self.cc.size(self.key), 1)
        v = self.cc.lpop_value(self.key)
        self.assertEqual(v, self.key)
        self.assertEqual(self.cc.size(self.key), 0)

    def test_set(self):
        pass


if __name__ == '__main__':
    unittest.main()
