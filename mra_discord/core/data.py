from __future__ import annotations
from typing import TypeVar, Union
import json

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class Savable:
    """
    Base class for savable objects. The idea is to create a custom container that saves its state
    to file as soon as it is changed, without the need to explicitly call a save function.
    """

    def __init__(self, parent=None, *, path: str = None):
        if parent is None:
            self._parent = self
        else:
            self._parent = parent

        self._path = path

        # used to control if changes should be saved immediately
        self._do_save = True

    @property
    def parent(self) -> Savable:
        return self._parent

    @property
    def do_save(self) -> bool:
        return self._do_save

    @do_save.setter
    def do_save(self, save: bool) -> None:
        self._do_save = save

    def save(self) -> None:
        if self._do_save:
            if self.parent == self:
                file = open(self._path, "w")
                json.dump(self, file)
                file.close()
            else:
                self.parent.save()


class DataDict(Savable, dict):

    def __init__(self, kwargs: dict, parent: Savable = None, *, path: str = None):
        # converts all elements recursively to data lists and data dicts
        for key in kwargs:
            kwargs[key] = convert(kwargs[key], self)

        dict.__init__(self, kwargs)
        Savable.__init__(self, parent, path=path)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, convert(value, self))
        self.save()

    def pop(self, key: _KT) -> _VT:
        value = dict.pop(self, key)
        self.save()
        return value


class DataList(Savable, list):

    def __init__(self, seq: list = (), parent: Savable = None, *, path: str = None):
        # converts all elements recursively to data lists and data dicts
        seq = [convert(s, self) for s in seq]

        list.__init__(self, seq)
        Savable.__init__(self, parent, path=path)

    def append(self, __object: _T) -> None:
        list.append(self, convert(__object, self))
        self.save()

    def remove(self, __value: _T) -> None:
        list.remove(self, __value)
        self.save()

    def pop(self, __index: int = ...) -> _T:
        element = list.pop(self, __index)
        self.save()
        return element


def convert(__object: _T, parent: Savable = None) -> Union[_T, DataList, DataDict]:
    """
    Converts lists into DataLists and dicts into DataDicts.
    """
    if isinstance(__object, dict):
        return DataDict(__object, parent)
    elif isinstance(__object, list):
        return DataList(__object, parent)
    return __object



