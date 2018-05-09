import yaml

from db_transfer.adapter_file import File


class YamlFile(File):

    file_extension = 'yaml'

    def load_file(self):
        with open(self.FILE_LOCAL, "rb+") as _file:
            file_contents = yaml.load(_file.read())
        return file_contents

    def dump_file(self, contents):
        with open(self.FILE_LOCAL, "w") as _file:
            yaml.dump(contents, _file, default_flow_style=False)
