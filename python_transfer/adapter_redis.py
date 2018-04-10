import redis
import ujson

from python_transfer.adapter import Adapter


class Redis(Adapter):
    """ Redis adapter.

    It connects to Redis database.
    """

    connection = {}

    def __init__(self, data_handler=None):
        self.data_handler = data_handler
        self.HOST = None
        self.PORT = None
        self.DB = None
        self._keys = None
        self.context_entered(False)
        self._pipeline = None

    def connect(self, host=None, port=None, db=None):
        self.HOST = host or self.data_handler.get_env('HOST')
        self.PORT = port or self.data_handler.get_env('PORT')
        self.DB = db or self.data_handler.get_env('DB')

        conn_key = str(self.HOST) + str(self.PORT) + str(self.DB)
        if not self.connection.get(conn_key):
            self.connection[conn_key] = redis.StrictRedis(host=self.HOST,
                                                          port=self.PORT,
                                                          db=self.DB,
                                                          decode_responses=True)
        return self.connection[conn_key]

    @property
    def __keys(self):
        if not self._keys:
            self._keys = RedisKeys(self.data_handler)
        return self._keys

    def contains(self, item):
        key = Redis.key(self.data_handler, item)
        return self.conn().exists(key)

    def conn_and_key(self, item):
        if self.data_handler is not None:
            key = Redis.key(self.data_handler, item)
        else:
            key = item
        conn = self.conn()
        return conn, key

    def get(self, item):
        conn, key = self.conn_and_key(item)

        if not conn.exists(key):
            return None

        _type = conn.type(key)
        if _type == 'string':
            n = conn.get(key)
            try:
                return int(n)
            except ValueError:
                return n
        elif _type == 'list':
            value = conn.lrange(key, 0, -1)
            lst = []
            for itm in value:
                if len(itm) > 0 and (itm[0] in ['[', '{']) and itm[-1] in [']', '}']:
                    lst.append(ujson.loads(itm))
                else:
                    lst.append(itm)
            return lst
        elif _type == 'hash':
            return RedisHash(self, conn, key)
        elif _type == 'set':
            return conn.smembers(key)

    def set(self, item, value):
        conn, key = self.conn_and_key(item)

        if self.context_entered():
            if not self._pipeline:
                self._pipeline = conn.pipeline()
            conn = self._pipeline

        if type(value) is str or type(value) is int:
            conn.set(key, value)
        elif type(value) is list and value:
            # lst = self.get(item) or []
            lst = []
            for itm in value:
                if type(itm) == list or type(itm) == dict:
                    lst.append(ujson.dumps(itm))
                else:
                    lst.append(itm)
            # conn.delete(key)
            conn.rpush(key, *lst)
        elif type(value) is dict and value:
            conn.hmset(key, value)

        self.__keys.add(item, conn)

    def delete(self, item):
        conn, key = self.conn_and_key(item)

        if self.context_entered():
            if not self._pipeline:
                self._pipeline = conn.pipeline()
            conn = self._pipeline

        conn.delete(key)
        self.__keys.remove(item, conn)

    def flush(self):
        self.conn().delete(self.data_handler.prefix)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def context_entered(self, entered=None):
        if entered is None:
            return self._context_entered
        else:
            self._context_entered = entered

    def exit(self, exc_type, exc_val, exc_tb):
        self._pipeline.execute()
        self._pipeline.__exit__(exc_type, exc_val, exc_tb)
        self._pipeline = None
        self.context_entered(False)

    def keys(self, full_key=False):
        keyset = []
        if full_key:
            key_prefix = Redis.key_prefix(self.data_handler) + ':'
        for k in self.__keys.all:
            if full_key:
                keyset.append(key_prefix + k)
            else:
                keyset.append(k)
        return keyset

    def custom_items(self, keys=None):
        data = []
        if keys is None:
            keys = self.keys()
        for key in keys:
            data.append((key, self.get(key)))
        return data


class RedisKeys(object):
    """ Used only for handling keys in Redis adapter

    Redis KEYS command is very dangerous to use in production environment,
    so to maintan the list of keys per redis instance all used keys
    are stored as set.
    """

    KEYS = 'keys'

    def __init__(self, redis_handler):
        self._redis_handler = redis_handler

    @property
    def key(self):
        return self._redis_handler.adapter.key_prefix(self._redis_handler) + ':' + self.KEYS

    @property
    def all(self):
        return self._redis_handler.adapter.conn().smembers(self.key)

    def add(self, key, conn=None):
        if conn is None:
            conn = self._redis_handler.adapter.conn()
        conn.sadd(self.key, key)

    def remove(self, key, conn=None):
        if conn is None:
            conn = self._redis_handler.adapter.conn()
        conn.srem(self.key, 0, key)


class RedisHash:

    def __init__(self, adapter, conn, key):
        self._key = key
        self._conn = conn
        self._adapter = adapter

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise Exception('Not a list')
        return self._conn.hget(self._key, item)

    def __setitem__(self, item, value):
        self._conn.hset(self._key, item, value)

    def __iter__(self):
        for item in self.keys():
            yield (item, self.__getitem__(item))

    def keys(self):
        return [item for item in self._conn.hkeys(self._key)]

    def items(self):
        return [(item, self.__getitem__(item)) for item in self.keys()]
