import os
import pytest

from db_transfer.transfer import Transfer, sent_env


def yaml_transfer():
    os.environ['yaml_file_path'] = './test_yaml.yaml'

    @sent_env('yaml', 'FILE_LOCAL', 'yaml_file_path')
    class TestHandlerYaml(Transfer):
        pass

    yaml_transfer = TestHandlerYaml(namespace='namespace_1', adapter_name='yaml')

    return yaml_transfer


@pytest.fixture()
def yaml_transfer_write():
    return yaml_transfer()


@pytest.fixture()
def yaml_transfer_read():
    return yaml_transfer()


def test_yaml_string(yaml_transfer_write, yaml_transfer_read):
    with yaml_transfer_write:
        yaml_transfer_write['key_1'] = 'value'
        yaml_transfer_write['key_2:key_3'] = 'value'
        yaml_transfer_write['key_4'] = 'value'
        yaml_transfer_write['key_2:key_5'] = 'value'

    assert str(yaml_transfer_read['key_1']) == 'value'
    assert str(yaml_transfer_read['key_2:key_3']) == 'value'
    assert str(yaml_transfer_read['key_4']) == 'value'
    assert str(yaml_transfer_read['key_2:key_5']) == 'value'


def test_yaml_list(yaml_transfer_write, yaml_transfer_read):
    with yaml_transfer_write:
        yaml_transfer_write['key_1:key_2'] = ['list_element_1', 'list_element_2']
        yaml_transfer_write['key_3:key_4'] = [['list_element_1', 'list_element_2']]
        yaml_transfer_write['key_5'] = [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]

    assert list(yaml_transfer_read['key_1:key_2']) == ['list_element_1', 'list_element_2']
    assert list(yaml_transfer_read['key_3:key_4']) == [['list_element_1', 'list_element_2']]
    assert list(yaml_transfer_read['key_5']) == [{'key': 'value', 'foo': 'bar'}, {'key': 'value'}]


def test_yaml_set(yaml_transfer_write, yaml_transfer_read):
    with yaml_transfer_write:
        yaml_transfer_write['key_1:key_2'] = set(['list_element_1', 'list_element_2'])

    assert set(yaml_transfer_read['key_1:key_2']) == {'list_element_1', 'list_element_2'}


def test_yaml_dict(yaml_transfer_write, yaml_transfer_read):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}

    with yaml_transfer_write:
        yaml_transfer_write['hash_key'] = test_dict

    assert yaml_transfer_read['hash_key'] == test_dict
    assert yaml_transfer_read['hash_key']['foo'] == test_dict['foo']
    assert yaml_transfer_read['hash_key']['doo'] == test_dict['doo']
    assert yaml_transfer_read['hash_key']['zoo'] == test_dict['zoo']

    for key, value in yaml_transfer_read['hash_key'].items():
        assert test_dict[key] == value


def test_yaml_iterator(yaml_transfer_write, yaml_transfer_read):
    test_dict = {'foo': 'bar', 'doo': {'goo': 'gar'}, 'zoo': [1, 2, 3, {'foo': 'bar'}]}

    with yaml_transfer_write:
        yaml_transfer_write['hash_key'] = test_dict

    for key, value in iter(yaml_transfer_read['hash_key'].items()):
        assert test_dict[key] == value


def test_yaml_delete(yaml_transfer_write, yaml_transfer_read):
    with yaml_transfer_write:
        yaml_transfer_write['some_key_1'] = 'some_value'

    assert str(yaml_transfer_read['some_key_1']) == 'some_value'

    with yaml_transfer_write:
        del yaml_transfer_write['some_key_1']

    assert yaml_transfer_read['some_key_1'] is None


def test_yaml_keys(yaml_transfer_write, yaml_transfer_read):
    with yaml_transfer_write:
        del yaml_transfer_write['key_2:key_4']
        del yaml_transfer_write['key_2:key_7:key_9']

    assert yaml_transfer_read.keys() == ['hash_key:doo:goo', 'hash_key:foo', 'hash_key:zoo',
                                         'key_1', 'key_2:key_3', 'key_2:key_5', 'key_3:key_4',
                                         'key_4', 'key_5', 'key_1:key_2', 'hash_key']
