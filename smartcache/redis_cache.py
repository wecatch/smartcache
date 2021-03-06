from __future__ import absolute_import, division, print_function, with_statement

import inspect
import hashlib
import logging
import functools
import random
from collections import namedtuple
from types import MethodType

try:
    import cPickle as pickle
except Exception as e:
    import pickle

import redis
from hash_ring import HashRing
from smartcache.commands import READ_COMMANDS


class Cache(object):

    def __getattr__(self, name):
        new_name = name.replace('_Cache', '', 1)
        if new_name.startswith('__'):
            command = new_name[2:]
            if command in READ_COMMANDS:
                redis_client = self.slave_connection()
            else:
                redis_client = self.master_connection()
            attr = getattr(redis_client, command, None)
            if attr is not None:
                return attr

        raise AttributeError('cache has no attribute %s'%name)

    def get_connection(self, host='localhost', port=6379, db=0):
        return redis.StrictRedis(host=host, port=port, db=db)

    def inject_connection(self, connection):
        self.get_connection = connection

    def master_connection(self):
        return self.get_connection()

    def slave_connection(self):
        return self.get_connection()

    def valid(self, key):
        """
        valid redis key and value
        """
        if key is None or key is '':
            return False
        return True

    def pack(self, *args):
        """pack args to redis key
        """
        return '_'.join(map(str, args))

    def unpack(self, key):
        """unpack redis key to tuple
        """
        return tuple(key.split('_'))

    def set(self, name, value):
        """redis set command
        """
        if not self.valid(value):
            return

        if not self.valid(name):
            return
        name = str(name)
        self.__set(name, self.dumps(value))

    def inc(self, key, amount=1):
        """inc command
        """
        return self.__incrby(str(key), amount)

    def hinc(self, name, key, amount=1):
        """hset hincrby command
        warnings: if the value has been serialized, be careful to call this command
        """
        return self.__hincrby(str(name), key, amount)

    def inc_score(self, name, value, amount=1):
        """sortedset h
        """
        return self.__zincrby(str(name), self.dumps(value), amount)

    def get(self, name):
        """redis get command
        """
        data = self.__get(str(name))
        try:
            return self.loads(data) if data else data
        except:
            return data

    def exists(self, name):
        """redis exists command
        """
        return bool(self.__exists(str(name)))

    def __contains__(self, item):
        return self.exists(item)

    def delete(self, name):
        """redis delete command
        """
        return self.__delete(str(name))

    def expire(self, name, expire):
        """redis expire command
        """
        return self.__expire(str(name), expire)

    def expireat(self, name, timestamp):
        """redis expireat command
        """
        return self.__expireat(str(name), timestamp)

    def persist(self, name):
        """redis persist command
        """
        return self.__persist(str(name))

    def move(self, name, db):
        """redis move command
        """
        return self.__move(str(name), db)

    def object(self, name, infotype='idletime'):
        """redis object command
        """
        return self.__object(infotype, str(name))

    def rename(self, name, newname):
        """redis rename command
        """
        return self.__rename(str(name), str(newname))

    def renamenx(self, name, newname):
        """redis renamenx command
        """
        return self.__renamenx(str(name), str(newname))

    def ttl(self, name):
        """redis ttl command
        """
        return self.__ttl(str(name))

    def type(self, name):
        """redis type command
        """
        return self.__type(str(name))

    def size(self, key):
        """:
        set: scard command
        zset: zcard command
        hash: hllen command
        list: llen command
        """
        ctype = self.__type(key)
        if ctype == 'set':
            return self.__scard(key)

        if ctype == 'zset':
            return self.__zcard(key)

        if ctype == 'hash':
            return self.__hlen(key)

        if ctype == 'string':
            raise ValueError('%s is string type' % key)

        return self.__llen(key)

    def append(self, name, value):
        """redis append command
        """
        return self.__append(str(name), value)

    def scan_db(self):
        start = 0
        result_length = 10
        while result_length:
            start, result = self.__scan(start)
            result_length = len(result)
            yield result

    def _update_hash(self, name, key, value):
        if not self.valid(name):
            return

        if not self.valid(key):
            return

        if not self.valid(value):
            return

        name, key = str(name), str(key)
        self.__hset(name, key, self.dumps(value))

    def hash(self, name, key=None, value=None):
        """hset and hget command
        """
        if key is None and value is None:
            return self._hash_all(name)

        if value is not None:
            return self._update_hash(name, key, value)
        else:
            data = self.__hget(str(name), key)
            try:
                return self.loads(data) if data else data
            except:
                return data

    def hash_keys(self, name):
        name = str(name)
        return self.__hkeys(name)

    def hash_values(self, name):
        name = str(name)
        result = self.__hvals(name)
        try:
            return [self.loads(i) for i in result]
        except:
            return result

    def hash_items(self, name):
        return self._hash_all(name).items()

    def _hash_all(self, name):
        result = self.__hgetall(str(name))
        try:
            for k, v in result.items():
                result[k] = pickle.loads(v)
        finally:
            return result

    def lupdate(self, name, data):
        """lpush command
        """
        self._update_list(name, data, self.__lpush)

    def rupdate(self, name, data):
        """rpush command
        """
        self._update_list(name, data, self.__rpush)

    def list(self, name, skip=0, limit=1):
        """lrange command
        :returns list value
        """
        return [self.loads(i) for i in self.__lrange(str(name), skip, skip+limit-1)]

    def rpop(self, name):
        """rpop command
        """
        return self._pop_list_value(name, self.__rpop)

    def lpop(self, name):
        """lpop command
        """
        return self._pop_list_value(name, self.__lpop)

    def _pop_list_value(self, name, func):
        data = func(str(name))
        if not data:
            return

        return self.loads(data)

    def _update_list(self, name, data, func):
        if not self.valid(name):
            return

        result = None
        if self._is_iterable(data):
            result = [self.dumps(i) for i in data]
        else:
            result = [self.dumps(data)]

        if not result:
            return
        name = str(name)
        try:
            func(name, *result)
        except Exception as e:
            [func(name, i) for i in result]


    @staticmethod
    def _is_iterable(data):
        return isinstance(data, list) or isinstance(data, tuple) or isinstance(data, set) or inspect.isgenerator(data)

    def members(self, name, count=1, with_all=False):
        """set srandmember command
        :return set members
        """
        count = abs(count)
        name = str(name)
        result = None
        try:
            if with_all:
                result = self.__smembers(name)  # return set
            else:
                result = self.__srandmember(name, count) # return list
        except:
            # Compatible for low version redis
            result = self.__srandmember(name) # return one value

        if result is None:
            return None

        if isinstance(result, list) or isinstance(result, set):
            return [self.loads(i) for i in result]

        return [self.loads(result)]

    def all(self, name):
        """set smembers command
        """
        return self.members(name, with_all=True)

    def sadd(self, name, member):
        return self.update_set(name, member)

    def update_set(self, name, member):
        if not self.valid(name):
            return

        name = str(name)
        if self._is_iterable(member):
            result = [self.dumps(i) for i in member]
            try:
                return self.__sadd(name, *result)
            except Exception as e:
                # Compatible for low version redis
                return sum([self.__sadd(name, i) for i in result])
        else:
            return self.__sadd(name, self.dumps(member))

    def contains(self, name, key):
        """implemented for sismember command and hexists command
        """
        ctype = self.__type(str(name))
        if ctype == 'set':
            return bool(self.__sismember(name, self.dumps(key)))

        if ctype == 'hash':
            return bool(self.__hexists(name, key))

        return False

    def move_set_member(self, src, dst, member):
        """set smove command
        """
        return self.__smove(str(src), str(dst), self.dumps(member))

    def pop_member(self, name, value=None):
        """srem command and zrem command
        """
        name = str(name)
        ctype = self.__type(name)
        if ctype == 'set':
            return self._pop_set(name, value) # return pop value number

        if ctype == 'zset':
            return self._pop_sortedset(name, value) # return pop value number

        return 0

    def _pop_sortedset(self, name, value):
        name = str(name)
        if self._is_iterable(value):
            result = [self.dumps(i) for i in value]
            try:
                return self.__zrem(name, *result)
            except Exception as e:
                return sum([self.__zrem(name, i) for i in result])
        else:
            return self.__zrem(name, self.dumps(value))

    def _pop_set(self, name, value):
        name = str(name)
        if self._is_iterable(value):
            try:
                return self.__srem(name, *[self.dumps(i) for i in value])
            except Exception as e:
                return sum([self.__srem(name, self.dumps(i)) for i in value])
        else:
            return self.__srem(name, self.dumps(value))

    def sortedset_members(self, name, skip=0, limit=1, min_score='-inf', max_score='inf', withscores=False):
        """sortedset members according to score
        """
        result = self.__zrangebyscore(str(name), float(min_score), float(max_score),
                                      start=skip, num=limit, withscores=withscores)
        if withscores:
            return [(self.loads(value), score) for value, score in result]

        return [self.loads(value) for value in result]

    def remove_member_with_score(self, name, min_score=0, max_score=0):
        return self.__zremrangebyscore(str(name), float(min_score), float(max_score))

    def remove_member_with_rank(self):
        raise NotImplementedError

    def score(self, name, key):
        return self.__zscore(str(name), self.dumps(key))

    def zadd(self, name, value, score):
        return self.update_sortedset(name, (value, score))

    def update_sortedset(self, name, value_list):
        """sortedset zadd command
        """
        if not self.valid(name):
            return

        if not self._is_iterable(value_list):
            return

        result = []
        if isinstance(value_list, tuple):
            result.append(value_list[1])
            result.append(self.dumps(value_list[0]))
        else:
            for value, score in value_list:
                result.append(score)
                result.append(self.dumps(value))

        if not result:
            return

        name = str(name)
        try:
            return self.__zadd(name, *result)
        except Exception as e:
            # Compatible for low version redis
            return sum([self.__zadd(name, *tuple(result[index:index+2])) for index in range(0, len(result), 2)])

    def loads(self, obj):
        """Override for object Deserialization
        """
        return pickle.loads(obj)

    def dumps(self, obj):
        """Override for object Serialization
        """
        return pickle.dumps(obj)


class ShardClient(object):

    """
    ::code-block
        servers = [
            {'name': 'server1', 'host': '192.168.0.246', 'port': 6379, 'db': 0, 'weight': 1},
            {'name': 'server2', 'host': '192.168.0.247', 'port': 6379, 'db': 0, 'weight': 1},
            {'name': 'server3', 'host': '192.168.0.248', 'port': 6379, 'db': 0, 'weight': 1},
            {'name': 'server4', 'host': '192.168.0.249', 'port': 6379, 'db': 0, 'weight': 1},
        ]
    """

    def __init__(self, servers):
        self._connections = {}
        hosts, weights = self.format_servers(servers)
        self._ring = HashRing(hosts, weights)
        self.build_connections(servers)

    def format_servers(self, servers):
        hosts = []
        weights = {}
        for s in servers:
            name = self.node_name(s)
            hosts.append(name)
            weights[name] = s['weight']

        return hosts, weights

    def node_name(self, s):
        return ('%s:%s:%s:%s')%(s['name'], s['host'], s['port'], s['db'])

    def build_connections(self, servers):
        for s in servers:
            self._connections[self.node_name(s)] = self.connect_redis(**s)

    def connect_redis(self, host='localhost', port=6379, db=0, **kwargs):
        return redis.StrictRedis(host=host, port=port, db=db)

    def get_server(self, key):
        return self._ring.get_node(key)

    def get_connection(self, key):
        node = self._ring.get_node(key)
        return self._connections[node]


def shard_cache_wrap(shard_cache, cc):
    def outwrapper(func):
        @functools.wraps(func)
        def innerwrapper(key, *args, **kwargs):
            connection = shard_cache.shard_client.get_connection(key)
            cc.inject_connection(lambda : connection)
            return func(key, *args, **kwargs)

        return innerwrapper

    return outwrapper


class ShardCache(object):

    slots = frozenset(['inject_connection', 'get_connection', 'master_connection', 'slave_connection'])

    def __init__(self, servers):
        self.shard_client = ShardClient(servers)

    def __getattr__(self, name):
        cc = self.get_cache()
        func = getattr(cc, name, None)
        if func is None or name in self.slots:
            raise AttributeError('ShardCache has no attribute %s'%name)

        return shard_cache_wrap(self, cc)(func)

    def get_cache(self):
        return Cache()


NodeClient = namedtuple('NodeClient', ['node_name', 'client'])

class MasterSlaveClient(object):

    """
    ::code-block
        servers = [
            {'name': 'server1', 'host': '192.168.0.246', 'port': 6379, 'db': 0, 'master': True},
            {'name': 'server2', 'host': '192.168.0.247', 'port': 6379, 'db': 0, 'slave': False},
            {'name': 'server3', 'host': '192.168.0.248', 'port': 6379, 'db': 0, 'slave': False},
            {'name': 'server4', 'host': '192.168.0.249', 'port': 6379, 'db': 0, 'slave': False},
        ]
    """

    def __init__(self, servers):
        self._master = None
        self._slave = []
        self._slave_range = []
        self.build_connections(servers)

    def node_name(self, s):
        return ('%s:%s:%s:%s')%(s['name'], s['host'], s['port'], s['db'])

    def build_connections(self, servers):
        for s in servers:
            nc = NodeClient(self.node_name(s), self.connect_redis(**s))
            if s.get('master'):
                self._master = nc
            else:
                self._slave.append(nc)

        self._slave_range = range(0, len(self._slave))

    def connect_redis(self, host='localhost', port=6379, db=0, **kwargs):
        return redis.StrictRedis(host=host, port=port, db=db)

    def get_master(self):
        return self._master.client

    def get_slave(self, key):
        index = self.hash_method(key)
        return self._slave[index].client

    def hash_method(self, key):
        return random.choice(self._slave_range)


def master_slave_cache_wrap(master_slave_cache, cc):
    def outwrapper(func):
        @functools.wraps(func)
        def innerwrapper(key, *args, **kwargs):
            connection = master_slave_cache.master_slave_client.get_slave(key)
            cc.slave_connection = MethodType(lambda self: connection, cc)
            return func(key, *args, **kwargs)

        return innerwrapper

    return outwrapper


class MasterSlaveCache(object):

    slots = frozenset(['inject_connection', 'get_connection', 'master_connection', 'slave_connection'])

    def __init__(self, servers):
        self.master_slave_client = MasterSlaveClient(servers)

    def __getattr__(self, name):
        cc = self.get_cache()
        cc.master_connection = MethodType(lambda x: self.master_slave_client.get_master(), cc)
        func = getattr(cc, name, None)
        if func is None or name in self.slots:
            raise AttributeError('ShardCache has no attribute %s'%name)

        return master_slave_cache_wrap(self, cc)(func)

    def get_cache(self):
        return Cache()


if __name__ == '__main__':
    cc = Cache()