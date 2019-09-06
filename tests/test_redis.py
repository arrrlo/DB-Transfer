import os
import pytest
import fakeredis

from db_transfer.adapter_redis import Redis
from db_transfer.transfer import Transfer, sent_env


@pytest.fixture()
def fake_redis(monkeypatch):
    fake_redis = lambda *args, **kwargs: fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(Redis, 'connect', fake_redis)
    #fake_redis().flushall()
    return fake_redis


@pytest.fixture()
def redis_transfer(fake_redis):
    os.environ['test_host_1'] = 'localhost'
    os.environ['test_port_1'] = '6379'
    os.environ['test_db_1'] = '0'

    @sent_env('redis', 'HOST', 'test_host_1')
    @sent_env('redis', 'PORT', 'test_port_1')
    @sent_env('redis', 'DB', 'test_db_1')
    class TestHandlerRedis_1(Transfer):
        pass

    redis_transfer = TestHandlerRedis_1(namespace='namespace_1', adapter_name='redis')

    return redis_transfer


def test_redis_string(redis_transfer):
    redis_transfer['key_1'] = 'value'
    redis_transfer['key_2:key_3'] = 'value'

    with redis_transfer:
        redis_transfer['key_4'] = 'value'
        redis_transfer['key_2:key_5'] = 'value'

    assert str(redis_transfer['key_1']) == 'value'
    assert str(redis_transfer['key_2:key_3']) == 'value'
    assert str(redis_transfer['key_4']) == 'value'
    assert str(redis_transfer['key_2:key_5']) == 'value'


def test_redis_list(redis_transfer):
    redis_transfer['key_6:key_7'] = ['list_element_1', 'list_element_2']

    with redis_transfer:
        redis_transfer['key_8:key_9'] = [['list_element_1', 'list_element_2']]
        redis_transfer['key_10'] = [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]

    assert list(redis_transfer['key_6:key_7']) == ['list_element_1', 'list_element_2']
    assert list(redis_transfer['key_8:key_9']) == [['list_element_1', 'list_element_2']]
    assert list(redis_transfer['key_10']) == [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]


def test_redis_set(redis_transfer):
    redis_transfer['key_11:key_12'] = set(['list_element_1', 'list_element_2'])

    assert set(redis_transfer['key_11:key_12']) == {'list_element_1', 'list_element_2'}


def test_redis_hash(redis_transfer):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}
    redis_transfer['hash_key'] = test_dict

    assert dict(redis_transfer['hash_key']) == test_dict
    assert redis_transfer['hash_key']['foo'] == test_dict['foo']
    assert redis_transfer['hash_key']['doo'] == test_dict['doo']
    assert redis_transfer['hash_key']['zoo'] == test_dict['zoo']

    for key, value in redis_transfer['hash_key']:
        assert test_dict[key] == value


def test_redis_hash_iterator(redis_transfer):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}
    redis_transfer['hash_key'] = test_dict

    for key, value in iter(redis_transfer['hash_key']):
        assert test_dict[key] == value


def test_redis_delete(redis_transfer):
    redis_transfer['some_key_1'] = 'some_value'
    assert str(redis_transfer['some_key_1']) == 'some_value'

    del redis_transfer['some_key_1']
    assert redis_transfer['some_key_1'] is None


def test_redis_keys(redis_transfer):
    assert redis_transfer.keys() == ['hash_key', 'key_1', 'key_10',
                                     'key_11:key_12', 'key_2:key_3',
                                     'key_2:key_5', 'key_4', 'key_6:key_7',
                                     'key_8:key_9']
    assert redis_transfer['key_2'].keys() == ['key_2:key_3', 'key_2:key_5']

    del redis_transfer['key_2:key_3']
    del redis_transfer['key_2:key_5']

    assert redis_transfer.keys() == ['hash_key', 'key_1', 'key_10',
                                     'key_11:key_12', 'key_4', 'key_6:key_7',
                                     'key_8:key_9']
