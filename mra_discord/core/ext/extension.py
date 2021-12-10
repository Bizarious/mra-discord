from typing import Optional, Any


class ExtensionPackage:

    def __init__(self, *,
                 cls: Any,
                 name: str,
                 auto_load=False,
                 can_unload=True
                 ):

        self._cls = cls

        if name is None:
            self._name = cls.__name__
        else:
            self._name = name

        self._auto_load = auto_load
        self._can_unload = can_unload

    @property
    def name(self):
        return self._name

    @property
    def cls(self):
        return self._cls

    @property
    def auto_load(self):
        return self._auto_load

    @property
    def can_unload(self):
        return self._can_unload


def extension(*,
              name: Optional[str] = None,
              auto_load: Optional[bool] = False,
              can_unload: Optional[bool] = True
              ):

    def dec(cls):
        return ExtensionPackage(cls=cls,
                                name=name,
                                auto_load=auto_load,
                                can_unload=can_unload
                                )
    return dec
    