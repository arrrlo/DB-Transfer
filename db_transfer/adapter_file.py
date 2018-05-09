import os

from db_transfer.adapter import Adapter


class File(Adapter):

    file_extension = None

    def __init__(self, transfer=None):
        self._transfer = transfer
        self._set_local_file_path()

    def _set_local_file_path(self):
        """
        Take from environment variable, create dirs and
        create file if doesn' exist.
        """

        self.FILE_LOCAL = self._transfer.get_env('FILE_LOCAL')

        if not self.FILE_LOCAL:
            filename = str(self._transfer.prefix) + '_' + \
                str(self._transfer.namespace) + '.' + \
                str(self.file_extension)
            self.FILE_LOCAL = os.path.join(os.path.expanduser("~"), filename)

        dirs = os.path.dirname(self.FILE_LOCAL)
        if not os.path.exists(dirs):
            os.makedirs(dirs)

        try:
            open(self.FILE_LOCAL, "rb+").close()
        except:
            open(self.FILE_LOCAL, "a").close()

    def connect(self):
        """
        Get all the contents from yaml file to memory.
        """

        file_contents = self.load_file()

        if file_contents:
            return self.transform_to_custom_dict(file_contents)
        else:
            return {}

    def transform_to_custom_dict(self, file_contents=None):
        def rek(val, contents, key):
            if type(val) == dict:
                for k, v in val.items():
                    if key == '':
                        key += k
                    else:
                        key += ':' + k
                    rek(v, contents, key)
                    key = ':'.join(key.split(':')[:-1])
            else:
                contents[key] = val

        contents = {}
        rek(file_contents, contents, '')

        return contents

    def transform_to_native_dict(self):
        def keyer(dat):
            k = keys.pop(0)
            #print(dat, k)
            # print(type(dat))
            if not k in dat:
                dat[k] = {}
            if len(keys) > 0 and isinstance(dat[k], dict):
                dat[k] = keyer(dat[k])
            else:
                dat[k] = value
            return dat

        data = {}
        for key, value in self.conn().items():
            keys = key.split(':')
            data = keyer(data)

        return data

    def sync(self):
        self.dump_file(self.transform_to_native_dict())

    def get(self, item):
        conn = self.conn()
        key = File.key(self._transfer, item)
        return conn.get(key)

    def set(self, item, value):
        key = File.key(self._transfer, item)
        self.conn()[key] = value

    def delete(self, item):
        key = File.key(self._transfer, item)
        try:
            del self.conn()[key]
        except:
            pass

    def keys(self):
        keyset = []
        key_prefix = File.key_prefix(self._transfer) + ':'
        return [k.replace(key_prefix, '') for k in self.conn().keys()]

    def custom_items(self):
        data = []
        for key in self.keys():
            data.append((key, self.get(key)))
        return data

    def exit(self, exc_type, exc_val, exc_tb):
        self.sync()

    def load_file(self):
        pass

    def dump_file(self, data):
        pass
