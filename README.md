<h1>DB Transfer</h1>

[![PyPI version](https://badge.fury.io/py/DB-Transfer.svg)](https://badge.fury.io/py/DB-Transfer)

<p>An easy way to manipulate data using key-value databases like Redis.<br/>
It is designed to support a number of databases, but currently Redis and yaml file are supported.</p>

<h2>INSTALL</h2>

```bash
pip install DB-Transfer
```

<h2>Design</h2>

<p>There are an adapter class for every database.<br/>
After instantiating Python Transfer using certain adapter_name, we can manipulate the<br/>
data from key-value database just like dictionaries: transfer[key] = value</p>

<h2>Keys</h2>

<p>Keys are created using prefix, namespace and item.<br/>
Example: data:USERS:arrrlo:full_name<br/>
(data is prefix, USERS is namespace and arrrlo:full_name is item)</p>

<h2><img src="https://cdn4.iconfinder.com/data/icons/redis-2/1451/Untitled-2-512.png" width="20" style="margin-right: 20px;" />
Redis Adapter:</h2>

<h3>Connect to Redis using environment variables</h3>
<p>Very handy when using in docker containers.</p>

```python
from db_transfer import Transfer, sent_env

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_DB'] = '0'

@sent_env('redis', 'HOST', 'REDIS_HOST')
@sent_env('redis', 'PORT', 'REDIS_PORT')
@sent_env('redis', 'DB', 'REDIS_DB')
class RedisTransfer(Transfer):

    def __init__(self, prefix=None, namespace=None):
        super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='redis')
```

<h3>Store data</h3>

```python
rt = RedisTransfer()
rt['my_key'] = 'some_string' # redis: "SET" "data:my_key" "some_string"

rt = RedisTransfer(namespace='my_namespace')
rt['my_key'] = 'some_string' # redis: "SET" "data:my_namespace:my_key" "some_string"

rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace')
rt['my_key'] = 'some_string' # redis: "SET" "my_prefix:my_namespace:my_key" "some_string"
```

<h3>Connect to Redis using class parameters</h3>

```python
class RedisTransfer(Transfer):

    def __init__(self, prefix, namespace, host, port, db):
        super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='redis')

        self.set_env('HOST', host)
        self.set_env('PORT', port)
        self.set_env('DB', db)
```

<h3>Store data</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

rt['my_key'] = 'some_string' # redis: "SET" "my_prefix:my_name_space:my_key" "some_string"
```

<h3>Fetch data</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

my_var = rt['my_key'] # redis: "GET" "my_prefix:my_namespace:my_key"
```

<h3>Delete data</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

del rt['my_key'] # redis: "DEL" "my_prefix:my_namespace:my_key"
```

<h3>Other data types</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

rt['my_key_1'] = [1,2,3,4] # redis: "RPUSH" "my_prefix:my_namespace:my_key_1" "1" "2" "3" "4"
rt['my_key_2'] = {'foo', 'bar'} # redis: "SADD" "my_prefix:my_namespace:my_key_2" "foo" "bar"
rt['my_key_3'] = {'foo': 'bar'} # redis: "HMSET" "my_prefix:my_namespace:my_key_3" "foo" "bar"

my_var_1 = list(rt['my_key_1']) # redis: "LRANGE" "my_prefix:my_namespace:my_key_1" "0" "-1"
my_var_2 = set(rt['my_key_2']) # redis: "SMEMBERS" "my_prefix:my_namespace:my_key_2"
my_var_3 = dict(rt['my_key_2']) # redis: "HGETALL" "my_prefix:my_namespace:my_key_3"
```

<h3>Redis hash data type</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

rt['my_key'] = {'foo': 'bar'} # redis: "HMSET" "my_prefix:my_namespace:my_key" "foo" "bar"

my_var = dict(rt['my_key']) # redis: "HGETALL" "my_prefix:my_namespace:my_key"
my_var = rt['my_key']['foo'] # redis: "HGET" "my_prefix:my_namespace:my_key" "foo"

rt['my_key']['boo'] = 'doo' # redis: "HSET" "my_prefix:my_namespace:my_key" "boo" "bar"
```

<h3>Multiple commands execution with context manager (only for set and delete)</h3>

```python
with RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0) as rt:
    rt['my_key_1'] = 'some_string'
    rt['my_key_2'] = [1,2,3,4]
    rt['my_key_3'] = {'foo': 'bar'}

# redis:
#
# "MULTI"
# "SET" "my_prefix:my_namespace:my_key_1" "some_string"
# "RPUSH" "my_prefix:my_namespace:my_key_2" "1" "2" "3" "4"
# "HMSET" "my_prefix:my_namespace:my_key_3" "foo" "bar"
# "EXEC"
```


<h3>Using iterators</h3>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

for key, value in iter(rt):
    # yields key and value of every key starting with my_prefix:my_namespace:


rt['my_key'] = {...} # saving a hash data (dict)

for key, value in iter(rt['my_key']):
    # yields key and value for every HGET in my_prefix:my_namespace:my_key
```


<h3>Keys</h3>

<p>Every key in Redis is stored in set in same Redis.<br/>
Example:</p>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

rt['key_1'] = 'value'
rt['key_2:key3'] = 'value'
rt['key_2:key4'] = 'value'
rt['key_2:key_5:key_6'] = 'value'
rt['key_2:key_5:key_7'] = 'value'
rt['key_2:key_5:key_8'] = 'value'
```

<p>So, the keys are "key_1", "key_2:key3", "key_2:key4", "key_2:key5:key_6", "key_2:key5:key_7", "key_2:key5:key_8".<br/>
They are not stored in one set, but different keys are stored i different sets:<br/>
'my_prefix:my_namespace': set({'key_1', 'key_2:keys'})<br/>
'my_prefix:my_namespace:key_2': set({'key_3', 'key_4', 'key_5:keys'})<br/>
'my_prefix:my_namespace:key_2:key_5': set({'key_6', 'key_7', 'key_8'})<br/><br/>

This is done this way so you can easily access data by keys fom any level recursively:</p>


```python
rt.keys()
# > ['key_1', 'key_2:key3', 'key_2:key4', 'key_2:key_5:key_6', 'key_2:key_5:key_7', 'key_2:key_5:key_8']

rt['key_2'].keys()
# > ['key_3', 'key_4', 'key_5:key_6', 'key_5:key_7', 'key_5:key_8']

rt['key_2:key_5'].keys()
# > ['key_6', 'key_7', 'key_8']
```


<h3>Real life examples</h3>

<p>Transfer all data from one Redis database to another:</p>

```python
rt_1 = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)
rt_2 = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='some_host', port=6379, db=0)

for key in rt_1.keys():
    rt_2[key] = rt_1[key]
```

<p>or if you want to insert data in one batch (read goes one by one):</p>

```python
with rt_2:
    for key in rt_1.keys():
        rt_2[key] = rt_1[key]
```

<p>Transfer data from one user to another:</p>

```python
rt_1 = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

for key in rt_1['arrrlo'].keys():
    rt_1['edi:' + key] = rt_1['arrrlo:' + key]
```

<p>Delete user from database:</p>

```python
rt_1 = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)

with rt_1:
    for key in rt_1['arrrlo'].keys():
        del rt_1['arrrlo:' + key]
```


<h2><img src="https://i2.wp.com/d2b12p2f0n03yd.cloudfront.net/wp-content/uploads/2016/03/13105859/yaml.png?fit=128%2C128" width="26" style="margin-right: 20px;" />
Yaml File Adapter:</h2>

<p>Initially the data from yaml file transferes from file to memory.<br/>
From there every read, write or delete runs until the sync() method<br/>
is called. Then the data from memory is transfered to yaml file.<br/>
sync() method could be called using context manager or manually.</p>

<h3>Define path to yaml file using environment variable</h3>
<p>Very handy when using in docker containers.</p>

```python
from db_transfer import Transfer, sent_env

os.environ['YAML_FILE_PATH'] = '/path/to/yaml/file.yaml'

@sent_env('yaml', 'FILE_LOCAL', 'YAML_FILE_PATH')
class YamlFileTransfer(Transfer):

    def __init__(self, prefix=None, namespace=None):
        super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='yaml')
```

<h3>Define path to yaml file using class parameter</h3>

```python
class YamlFileTransfer(Transfer):

    def __init__(self, prefix, namespace, yaml_file_path):
        super().__init__(prefix=str(prefix), namespace=namespace, adapter_name='yaml')

        self.set_env('FILE_LOCAL', yaml_file_path)
```

<h3>Write and delete data</h3>
<p>Data could be written using context manager or sync() method.</p>

```python
yt = YamlFileTransfer(prefix='my_prefix', namespace='my_namespace', yaml_file_path='/path/')

with yt:
    yt['my_key_1'] = 'some_string'

yt['my_key_2'] = 'some_string'
yt.sync()

with yt:
    del yt['my_key_1']

del yt['my_key_2']
yt.sync()
```

<h3>Real life examples</h3>

<p>Backup user data from Redis to yaml file:</p>

```python
rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)
yt = YamlFileTransfer(prefix='my_prefix', namespace='my_namespace', yaml_file_path='/path/')

for key in rt['arrrlo'].keys():
    yt['arrrlo:' + key] = rt['arrrlo:' + key]

# or (depends on how you use prefix and namespace):

rt = RedisTransfer(prefix='users', namespace='arrrlo', host='localhost', port=6379, db=0)
yt = YamlFileTransfer(prefix='users', namespace='arrrlo', yaml_file_path='/path/')

for key in rt.keys():
    yt[key] = rt[key]

# or:

rt = RedisTransfer(prefix='my_prefix:my_namespace', namespace='arrrlo', host='localhost', port=6379, db=0)
yt = YamlFileTransfer(prefix='my_prefix:my_namespace', namespace='arrrlo', yaml_file_path='/path/')

for key in rt.keys():
    yt[key] = rt[key]

# or:

rt = RedisTransfer(prefix='my_prefix', namespace='my_namespace', host='localhost', port=6379, db=0)
yt = YamlFileTransfer(prefix='my_prefix:my_namespace', namespace='arrrlo', yaml_file_path='/path/')

for key in rt.keys():
    yt[key] = rt['arrrlo:' + key]
```
