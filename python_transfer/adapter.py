class Adapter(object):
    """ Mixin class with main adapter functionalities.

    Every adapter that uses this mixin needs to define getter and setter methods.
    """

    _connection = {}

    @staticmethod
    def key_prefix(data_handler):
        if not data_handler.namespace:
            return data_handler.prefix
        else:
            return data_handler.prefix + ':' + data_handler.namespace

    def conn(self, *args, **kwargs):
        key = Adapter.key_prefix(self.data_handler) + ':' + self.data_handler.adapter_name
        if not Adapter._connection.get(key):
            Adapter._connection[key] = self.connect(*args, **kwargs)
        return Adapter._connection[key]

    @staticmethod
    def key(data_handler, item=None):
        key = Adapter.key_prefix(data_handler)
        if item is not None:
            key += ':' + str(item)
        return key

    @staticmethod
    def store(data_handler, file_contents=None):
        global key
        global contents

        def rek(val):
            global key
            global contents
            if type(val) == dict:
                for k, v in val.items():
                    if key == '':
                        key += k
                    else:
                        key += ':' + k
                    rek(v)
                    key = ':'.join(key.split(':')[:-1])
            else:
                contents[key] = val

        contents = {}
        key = ''
        rek(file_contents)

        return contents