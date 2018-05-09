import redis
import ujson

from db_transfer.adapter import Adapter


class Redis(Adapter):
    """ Redis adapter.

    It connects to Redis database.
    """

    connection = {}

    def __init__(self, transfer=None):
        self._transfer = transfer
        self.HOST = None
        self.PORT = None
        self.DB = None
        self.context_entered(False)
        self._pipeline = None

    def connect(self, host=None, port=None, db=None):
        self.HOST = host or self._transfer.get_env('HOST')
        self.PORT = port or self._transfer.get_env('PORT')
        self.DB = db or self._transfer.get_env('DB')

        conn_key = str(self.HOST) + str(self.PORT) + str(self.DB)
        if not self.connection.get(conn_key):
            self.connection[conn_key] = redis.StrictRedis(host=self.HOST,
                                                          port=self.PORT,
                                                          db=self.DB,
                                                          decode_responses=True)
        return self.connection[conn_key]

    @property
    def _keys(self):
        return RedisKeys(self._transfer)

    def contains(self, item):
        key = Redis.key(self._transfer, item)
        return self.conn().exists(key)

    def conn_and_key(self, item):
        key = Redis.key(self._transfer, item)
        conn = self.conn()
        return conn, key

    def get(self, item):
        conn, key = self.conn_and_key(item)

        if not conn.exists(key):
            return None

        _type = conn.type(key)

        if _type == 'string':
            return String(self, item)
        elif _type == 'list':
            return List(self, item)
        elif _type == 'hash':
            return Hash(self, item)
        elif _type == 'set':
            return Set(self, item)
        else:
            raise Exception('Unknown data type to fetch')

    def set(self, item, value):
        conn, key = self.conn_and_key(item)

        if self.context_entered():
            if not self._pipeline:
                self._pipeline = conn.pipeline()
            conn = self._pipeline

        if type(value) in [str, int, None, True, False]:
            conn.set(key, value)

        elif type(value) in [list, tuple]:
            lst = []
            for itm in value:
                if type(itm) in [list, set, dict]:
                    lst.append(ujson.dumps(itm))
                else:
                    lst.append(itm)
            conn.rpush(key, *lst)

        elif type(value) is dict:
            dct = {}
            for k, val in value.items():
                if type(val) in [list, set, dict]:
                    dct[k] = ujson.dumps(val)
                else:
                    dct[k] = val
            conn.hmset(key, dct)

        elif type(value) is set:
            lst = []
            for itm in value:
                if type(itm) in [list, set, dict]:
                    lst.append(ujson.dumps(itm))
                else:
                    lst.append(itm)
            conn.sadd(key, *lst)

        else:
            raise Exception('Unknown data type to save')

        self._keys.add(item, conn)

    def delete(self, item):
        conn, key = self.conn_and_key(item)

        if self.context_entered():
            if not self._pipeline:
                self._pipeline = conn.pipeline()
            conn = self._pipeline

        conn.delete(key)
        self._keys.remove(item)

    def flush(self):
        self.conn().delete(self._transfer.prefix)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def exit(self, exc_type, exc_val, exc_tb):
        self._pipeline.execute()
        self._pipeline.__exit__(exc_type, exc_val, exc_tb)
        self._pipeline = None
        self.context_entered(False)

    def keys(self):
        return self._keys.all()

    def custom_items(self, keys=None):
        data = []
        if keys is None:
            keys = self.keys()
        for key in keys:
            data.append((key, self.get(key)))
        return data

    def sync(self):
        pass


class RedisKeys(object):
    """ Used only for handling keys in Redis adapter

    Redis KEYS command is very dangerous to use in production environment,
    so to maintan the list of keys per redis instance all used keys
    are stored as set.
    """

    def __init__(self, transfer):
        self._transfer = transfer

    @property
    def prefix(self):
        return self._transfer.adapter.key_prefix(self._transfer)

    def all(self, start_key=None):
        def search_keys(k, keyset):
            if k:
                search_key = prefix + ':' + k
            else:
                search_key = prefix

            for key in conn.smembers(search_key):
                if k:
                    key = k + ':' + key
                if key[-5:] == ':keys':
                    keyset = search_keys(key[:-5], keyset)
                else:
                    keyset.append(key)
            return keyset

        conn = self._transfer.adapter.conn()
        prefix = self._transfer.adapter.key_prefix(self._transfer)

        keyset = search_keys(start_key, [])

        return sorted(keyset)

    def add(self, item, conn=None):
        if conn is None:
            conn = self._transfer.adapter.conn()

        prefix = self.prefix
        splitted_item = item.split(':')

        with conn.pipeline() as pipe:
            while splitted_item:
                sufix = splitted_item.pop(0)
                if splitted_item:
                    pipe.sadd(prefix, sufix + ':keys')
                else:
                    pipe.sadd(prefix, sufix)
                prefix += ':' + sufix
            pipe.execute()

    def remove(self, item):
        conn = self._transfer.adapter.conn()
        prefix = self.prefix + ':' + item
        key = ':'.join(prefix.split(':')[:-1])
        conn.srem(key, item.split(':')[-1])


class RedisDataType(object):

    def __init__(self, adapter, item):
        self._item = item
        self._adapter = adapter
        self._conn, self._key = adapter.conn_and_key(item)

    def keys(self):
        try:
            return list(self._adapter._keys.all(self._item))
        except redis.exceptions.ResponseError:
            return list()


class String(RedisDataType):

    def __str__(self):
        _str = self._conn.get(self._key)
        try:
            return int(_str)
        except ValueError:
            return str(_str)

    __repr__ = __str__


class List(RedisDataType):

    def __iter__(self):
        self._values = list(self._conn.lrange(self._key, 0, -1))
        return self

    def __next__(self):
        try:
            value = self._values.pop(0)
            try:
                return ujson.loads(value)
            except:
                return value
        except IndexError:
            raise StopIteration()

    next = __next__


class Hash(RedisDataType):

    def keys(self):
        return [item for item in self._conn.hkeys(self._key)]

    def items(self):
        return [(item, self.__getitem__(item)) for item in self.keys()]

    def __getitem__(self, item):
        try:
            return ujson.loads(self._conn.hget(self._key, item))
        except:
            return self._conn.hget(self._key, item)

    def __setitem__(self, item, value):
        if type(val) == list or type(val) == dict:
            value = ujson.dumps(value)
        self._conn.hset(self._key, item, value)

    def __iter__(self):
        self._keys = self.keys()
        return self

    def __next__(self):
        try:
            item = self._keys.pop(0)
            return (item, self.__getitem__(item))
        except IndexError:
            raise StopIteration()

    next = __next__


class Set(RedisDataType):

    def __iter__(self):
        self._values = list(self._conn.smembers(self._key))
        return self

    def __next__(self):
        try:
            value = self._values.pop(0)
            try:
                return ujson.loads(value)
            except:
                return value
        except IndexError:
            raise StopIteration()

    next = __next__
