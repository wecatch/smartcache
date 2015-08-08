#-*- conding:utf-8-*-

import time

class DataObject(object):
    '''
    object cahced by app
    '''
    __slots__ = ['name', 'expire', '_value', 'last_visit_atime', 'last_update_atime']

    def __init__(self, name, value=None, expire=24*3600):
        self.name = name
        self.expire = expire
        self.last_visit_atime = time.time()
        self.last_update_atime = time.time()
        self._value = value

    def is_expired(self):
        return time.time() - self.last_update_atime > self.expire

    def set_value(self, value):
        self.last_update_atime = time.time()
        self._value = value

    def get_value(self):
        self.last_visit_atime = time.time()
        return self._value


class Cache(object):
    __data = {}

    @staticmethod
    def pack(*args):
        return '_'.join(map(str, args))

    @staticmethod
    def unpack(key):
        return tuple(key.split('_'))

    @staticmethod
    def set(key, value, expire=24*3600):
        if not hash(key):
            raise ValueError('%s is not hashable' % key)

        if key not in Cache.__data:
            Cache.__data[key] = DataObject(key, value, expire)

        Cache.__data[key].set_value(value)

    @staticmethod
    def get(key):
        if key not in Cache.__data:
            return None

        if Cache.__data[key].is_expired():
            del Cache.__data[key]
            return None

        return Cache.__data[key].get_value()

    def __contains__(self, item):
        return item and item in Cache.__data

    @staticmethod
    def exists(name):
        return name and name in Cache.__data

    @staticmethod
    def delete(name):
        Cache.__data.pop(name, None)

if __name__ == '__main__':
    pass