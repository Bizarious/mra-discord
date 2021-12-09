class ExtensionPackage:

    def __init__(self, cls, name):
        self._cls = cls
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def cls(self):
        return self._cls


def extension(cls):
    return ExtensionPackage(cls, cls.__name__)
    