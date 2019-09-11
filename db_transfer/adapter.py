class Adapter(object):
    """ Mixin class with main adapter functionalities.
    Every adapter that uses this mixin needs to define getter and setter methods.
    """

    @staticmethod
    def key_prefix(transfer):
        prefix_list = []
        if transfer.namespace:
            prefix_list.append(transfer.prefix)
        if transfer.namespace:
            prefix_list.append(transfer.namespace)
        return ':'.join(prefix_list)

    @staticmethod
    def key(transfer, item=None):
        key_list = []
        prefix = Adapter.key_prefix(transfer)
        if prefix:
            key_list.append(prefix)
        if item:
            key_list.append(item)
        return ':'.join(key_list)

    def conn(self, *args, **kwargs):
        return self.connect(*args, **kwargs)

    def context_entered(self, entered=None):
        if entered is None:
            return self._context_entered
        else:
            self._context_entered = entered
