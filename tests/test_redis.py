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
def test_handler_redis(fake_redis):
    os.environ['test_host_1'] = 'localhost'
    os.environ['test_port_1'] = '6379'
    os.environ['test_db_1'] = '0'

    @sent_env('redis', 'HOST', 'test_host_1')
    @sent_env('redis', 'PORT', 'test_port_1')
    @sent_env('redis', 'DB', 'test_db_1')
    class TestHandlerRedis_1(Transfer):
        pass

    test_handler_redis = TestHandlerRedis_1(namespace='namespace_1', adapter_name='redis')

    return test_handler_redis


def test_redis_write(test_handler_redis):
    with test_handler_redis:
        test_handler_redis['some_key_1'] = 'some_value'
        test_handler_redis['some_key_2:some_key_2'] = 'some_value'
        test_handler_redis['some_key_3:some_key_3'] = ['list_element_1', 'list_element_2']
        test_handler_redis['some_key_4:some_key_4'] = [['list_element_1', 'list_element_2']]
        test_handler_redis['some_key_5'] = {'key': 'value'}
        test_handler_redis['some_key_6'] = [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]

    assert test_handler_redis['some_key_1'] == 'some_value'
    assert test_handler_redis['some_key_2:some_key_2'] == 'some_value'
    assert test_handler_redis['some_key_3:some_key_3'] == ['list_element_1', 'list_element_2']
    assert test_handler_redis['some_key_4:some_key_4'] == [['list_element_1', 'list_element_2']]
    assert dict(test_handler_redis['some_key_5']) == {'key': 'value'}
    assert test_handler_redis['some_key_6'] == [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]


def test_redis_delete(test_handler_redis):
    with test_handler_redis:
        test_handler_redis['some_key_1'] = 'some_value'

    assert test_handler_redis['some_key_1'] == 'some_value'

    with test_handler_redis:
        del test_handler_redis['some_key_1']

    assert test_handler_redis['some_key_1'] is None
