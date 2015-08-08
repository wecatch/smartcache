
import inspect
import warnings
try:
    import cPickle as pickle 
except Exception as e:
    import pickle

import redis
from turbo.log import getLogger

logger = getLogger('smartcache')


class Cache(object):

    def __getattr__(self, name):
        new_name = name.replace('_Cache', '', 1)
        redis_client = self.get_connection(name=name)
        if new_name.startswith('__'):
            attr = getattr(redis_client, new_name[2:], None)
            if attr is not None:
                return attr

        return getattr(Cache, name)

    def get_connection(self, host='localhost', port=6379, db=0, name=None):
        return redis.StrictRedis(host=host, port=port, db=db)

    def inject_connection(self, connection):
        self.get_connection = connection

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

    def set(self, name, value, expire=86400):
        """redis set command
        """
        if not self.valid(value):
            return

        if not self.valid(name):
            return
        name = str(name)
        self.__set(name, self.dumps(value))
        self.__expire(name, expire)

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
            result_length = len(result_length)
            yield result

    def _update_dict(self, name, key, value, expire=86400):
        if not self.valid(name):
            return

        if not self.valid(key):
            return

        if not self.valid(value):
            return

        name, key = str(name), str(key)
        self.__hset(name, key, self.dumps(value))
        self.__expire(name, expire)

    def dict(self, name, key, value=None, expire=86400):
        """hset and hget command
        """
        if value is not None:
            return self._update_dict(name, key, value, expire)
        else:
            data = self.__hget(str(name), key)
            try:
                return self.loads(data) if data else data
            except:
                return data

    def lupdate(self, name, data, expire=86400):
        """lpush command
        """
        self._update_list(name, data, self.__lpush)

    def rupdate(self, name, data, expire=86400):
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

    def _update_list(self, name, data, func, expire=86400):
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

        self.__expire(name, expire)

    @staticmethod
    def _is_iterable(data):
        return isinstance(data, list) or isinstance(data, tuple) or inspect.isgenerator(data)

    def members(self, name, count=1):
        """set srandmember command
        :return set members
        """
        count = abs(count)
        name = str(name)
        try:
            result = self.__srandmember(name, count)
        except:
            # Compatible for low version redis
            result = self.__srandmember(name)

        if result is None:
            return None

        if isinstance(result, list):
            return [self.loads(i) for i in result]

        return [self.loads(result)]

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

    def update_sortedset(self, name, value_list, expire=86400):
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
        self.__expire(name, expire)
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


if __name__ == '__main__':
    cc = Cache()