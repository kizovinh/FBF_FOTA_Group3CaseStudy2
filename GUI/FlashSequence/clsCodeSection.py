class CodeSection:
    def __init__(self, start_address, end_address, size, name):
        self._start_address = start_address
        self._end_address   = end_address
        self._size          = size
        self._name          = name

    @property
    def start_address(self):
        return self._start_address

    @start_address.setter
    def start_address(self, value):
        self._start_address = value

    @property
    def end_address(self):
        return self._end_address

    @end_address.setter
    def end_address(self, value):
        self._end_address = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self.size = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value