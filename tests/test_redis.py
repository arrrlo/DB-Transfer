import os
import pytest
import fakeredis

from python_transfer.adapter_redis import Redis
from python_transfer.handler import Transfer, sent_env


@pytest.fixture()
def fake_redis(monkeypatch):
    fake_redis = lambda *args, **kwargs: fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(Redis, 'connect', fake_redis)
    fake_redis().flushall()
    return fake_redis


@pytest.fixture()
def redis_handler(fake_redis):
    os.environ['test_host_1'] = 'localhost'
    os.environ['test_port_1'] = '6379'
    os.environ['test_db_1'] = '0'

    @sent_env('redis', 'HOST', 'test_host_1')
    @sent_env('redis', 'PORT', 'test_port_1')
    @sent_env('redis', 'DB', 'test_db_1')
    class TestHandlerRedis_1(Transfer):
        pass

    redis_handler = TestHandlerRedis_1(namespace='namespace_1', adapter_name='redis')

    return redis_handler


def test_redis_write(redis_handler):
    redis_handler['some_key_1'] = 'some_value'
    redis_handler['some_key_2:some_key_2'] = 'some_value'
    redis_handler['some_key_3:some_key_3'] = ['list_element_1', 'list_element_2']

    with redis_handler:
        redis_handler['some_key_4:some_key_4'] = [['list_element_1', 'list_element_2']]
        redis_handler['some_key_5'] = {'key': 'value'}
        redis_handler['some_key_6'] = [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]

    assert redis_handler['some_key_1'] == 'some_value'
    assert redis_handler['some_key_2:some_key_2'] == 'some_value'
    assert redis_handler['some_key_3:some_key_3'] == ['list_element_1', 'list_element_2']
    assert redis_handler['some_key_4:some_key_4'] == [['list_element_1', 'list_element_2']]
    assert dict(redis_handler['some_key_5']) == {'key': 'value'}
    assert redis_handler['some_key_6'] == [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]


def test_redis_delete(redis_handler):
    redis_handler['some_key_1'] = 'some_value'
    assert redis_handler['some_key_1'] == 'some_value'

    del redis_handler['some_key_1']
    assert redis_handler['some_key_1'] is None


def test_redis_hash(redis_handler):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}
    redis_handler['hash_key'] = test_dict

    assert dict(redis_handler['hash_key']) == test_dict
    assert redis_handler['hash_key']['foo'] == test_dict['foo']
    assert redis_handler['hash_key']['doo'] == test_dict['doo']
    assert redis_handler['hash_key']['zoo'] == test_dict['zoo']


def test_redis_hash_iterator(redis_handler):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}
    redis_handler['hash_key'] = test_dict

    for key, value in redis_handler['hash_key']:
        assert test_dict[key] == value
