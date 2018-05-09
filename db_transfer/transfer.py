import os
import six

if six.PY2:
    from UserDict import DictMixin
elif six.PY3:
    from collections import MutableMapping as DictMixin

from db_transfer.adapter_redis import Redis
from db_transfer.adapter_yaml import YamlFile


ADAPTER_CLASSES = {
    'redis': Redis,
    'yaml': YamlFile,
}


class sent_env(object):
    """ Decorator class for setting the connection params.

    DataHandler needs connection to the database.
    This class is used to set those params from environment variables.

    Check the example at the bottom to see how it is used.
    """

    def __init__(self, adapter_name,
                 adapter_var_name,
                 env_var_name,
                 fallback_env_var_name=''):
        self.adapter_name = adapter_name
        self.adapter_var_name = adapter_var_name
        self.env_var_name = env_var_name
        self.fallback_env_var_name = fallback_env_var_name

    def __call__(self, data_handler_class):
        if data_handler_class.__name__ not in data_handler_class.adapter_vars:
            data_handler_class.adapter_vars[data_handler_class.__name__] = {}

        if self.adapter_name not in data_handler_class.adapter_vars[data_handler_class.__name__]:
            data_handler_class.adapter_vars[data_handler_class.__name__][self.adapter_name] = {}

        value = os.environ.get(self.env_var_name, os.environ.get(self.fallback_env_var_name))
        data_handler_class.adapter_vars[data_handler_class.__name__] \
                                       [self.adapter_name] \
                                       [self.adapter_var_name] = value
        return data_handler_class


class Transfer(DictMixin, object):
    """ Main class with wich the data handling object is instantiated.

    It is a MutableMapping and a factory.
    It instantiates one of the Adapter classes according to the adapter_name.

    Check the example at the bottom to see how it is used.
    """

    adapter_vars = {}

    def __init__(self, prefix='data', namespace=None, adapter_name=None):
        self.adapter_name = str(adapter_name)
        self.adapter_object = None
        self.prefix = prefix
        self.data_for(namespace)

    def set_env(self, adapter_var_name, value):
        if self.__class__.__name__ not in self.adapter_vars:
            self.adapter_vars[self.__class__.__name__] = {}

        if self.adapter_name not in self.adapter_vars[self.__class__.__name__]:
            self.adapter_vars[self.__class__.__name__][self.adapter_name] = {}

        self.adapter_vars[self.__class__.__name__]\
                         [self.adapter_name]\
                         [adapter_var_name] = value

    def get_env(self, adapter_var_name):
        return self.adapter_vars.get(self.__class__.__name__, {}) \
                                .get(self.adapter_name, {}) \
                                .get(adapter_var_name)

    def data_for(self, namespace):
        self.namespace = namespace
        return self

    @property
    def adapter(self):
        return self.adapter_object or self.inst_adapter()

    def inst_adapter(self):
        if not self.adapter_name:
            raise Exception("Data handler adapter not set.")

        try:
            Adapter = ADAPTER_CLASSES[self.adapter_name.lower()]
        except KeyError:
            raise Exception("Unknown adapter: " + str(self.adapter_name))

        self.adapter_object = Adapter(self)

        return self.adapter_object

    def keys(self):
        return self.adapter.keys()

    def items(self):
        return self.adapter.custom_items()

    def __getitem__(self, key):
        return self.adapter.get(key)

    def __setitem__(self, key, value):
        self.adapter.set(key, value)

    def __delitem__(self, key):
        self.adapter.delete(key)

    def __enter__(self):
        self.adapter.context_entered(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.adapter.exit(exc_type, exc_val, exc_tb)

    def __len__(self):
        return len(self.adapter.keys())

    def __iter__(self):
        for key in self.adapter.keys():
            yield (key, self.__getitem__(key))

    def __del__(self):
        pass
