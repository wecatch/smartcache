#-*- conding:utf-8-*-

import time

class DataObject(object):
    '''
    object cahced by app
    '''
    __slots__ = ['name', 'expire', '_value', '_last_visit_atime', '_last_update_atime']

    def __init__(self, name, value=None, expire=24*3600):
        self.name = name
        self.expire = expire
        self._last_visit_atime = time.time()
        self._last_update_atime = time.time()
        self._value = value

    def is_expired(self):
        return time.time() - self._last_visit_atime > self.expire

    def set_value(self, value):
        self._last_update_atime = time.time()
        self._value = value

    def get_value(self):
        self._last_visit_atime = time.time()
        return self._value


class Cache(object):
    __data = {}

    @staticmethod
    def key(*args):
        return '_'.join(map(str, args))

    @staticmethod
    def unpack_key(key):
        return tuple(key.split('_'))

    @staticmethod
    def set_value(key, value, expire=24*3600):
        if not hash(key):
            raise ValueError('%s name is not hashable' % key)

        if key not in Cache.__data:
            Cache.__data[key] = DataObject(key, value, expire)

        Cache.__data[key].set_value(value)

    @staticmethod
    def get_value(key):
        if key not in Cache.__data:
            return None

        return Cache.__data[key].get_value()

    @staticmethod
    def exists(name):
        return name and name in Cache.__data

    @staticmethod
    def delete(name):
        Cache.__data.pop(name, None)

if __name__ == '__main__':
    pass