<h1>Python Transfer</h1>

<p>An easy way to fetch and store data from and to key-value databases like Redis.<br/>
It is designed to have number of database adapters, but currently is has only Redis adapter.</p>

<h2>INSTALL (Python 3.x)</h2>

```bash
pip install git+git://github.com/arrrlo/python-transfer@master
```

<h2>USAGE</h2>

```python
from python_transfer import Transfer, sent_env

# using environment variables for connecting to database:

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_DB'] = '0'

@sent_env('redis', 'HOST', 'REDIS_HOST')
@sent_env('redis', 'PORT', 'REDIS_PORT')
@sent_env('redis', 'DB', 'REDIS_DB')
class RedisTransfer(Transfer):
    pass

rt = RedisTransfer(adapter_name='redis')
rt['my_key'] = 'some_string' # redis: "SET" "data:my_key" "some_string"

rt = RedisTransfer(namespace='my_namespace', adapter_name='redis')
rt['my_key'] = 'some_string' # redis: "SET" "data:my_name_space:my_key" "some_string"

rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', adapter_name='redis')
rt['my_key'] = 'some_string' # redis: "SET" "my_prefix:my_name_space:my_key" "some_string"
```

```python
# fetch data:

my_var = rt['my_key'] # redis: "GET" "my_prefix:my_name_space:my_key"
```

```python
# delete data:

del rt['my_key'] # redis: "DEL" "my_prefix:my_name_space:my_key"
```

```python
# without environment variables for connecting to database:

class RedisTransfer(Transfer):

    def __init__(self, prefix, namespace, host, port, db):
        super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='redis')

        self.set_env('HOST', host)
        self.set_env('PORT', port)
        self.set_env('DB', db)

rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', adapter_name='redis', \
                   host='localhost', port=6379, db=0)

rt['my_key'] = 'some_string' # redis: "SET" "my_prefix:my_name_space:my_key" "some_string"
```

```python
# other data types:

rt['my_key_1'] = [1,2,3,4] # redis: "RPUSH" "my_prefix:my_name_space:my_key" "1" "2" "3" "4"
rt['my_key_2'] = {'foo': 'bar'} # redis: "HMSET" "my_prefix:my_name_space:my_key" "foo" "bar"

my_var_1 = rt['my_key_1'] # redis: "LRANGE" "my_prefix:my_name_space:my_key_1" "0" "-1"
my_var_2 = rt['my_key_2'] # redis: "HGETALL" "my_prefix:my_name_space:my_key_2"
```

```python
# using redis pipeline (multiple commands execution, only for set and delete):

with rt:
    rt['my_key_1'] = 'some_string'
    rt['my_key_2'] = [1,2,3,4]
    rt['my_key_3'] = {'foo': 'bar'}
```
