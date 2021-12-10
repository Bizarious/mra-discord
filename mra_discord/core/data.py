from __future__ import annotations
from typing import TypeVar, Union
from threading import Lock
import json
import os

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

        # a lock for thread safety
        self._lock = Lock()

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
        self._lock.acquire()

        dict.__setitem__(self, key, convert(value, self))
        self.save()

        self._lock.release()

    def pop(self, key: _KT) -> _VT:
        self._lock.acquire()

        value = dict.pop(self, key)
        self.save()

        self._lock.release()

        return value


class DataList(Savable, list):

    def __init__(self, seq: list = (), parent: Savable = None, *, path: str = None):
        # converts all elements recursively to data lists and data dicts
        seq = [convert(s, self) for s in seq]

        list.__init__(self, seq)
        Savable.__init__(self, parent, path=path)

    def append(self, __object: _T) -> None:
        self._lock.acquire()

        list.append(self, convert(__object, self))
        self.save()

        self._lock.release()

    def remove(self, __value: _T) -> None:
        self._lock.acquire()

        list.remove(self, __value)
        self.save()

        self._lock.release()

    def pop(self, __index: int = ...) -> _T:
        self._lock.acquire()

        element = list.pop(self, __index)
        self.save()

        self._lock.release()

        return element


def convert(__object: _T, parent: Savable = None, path: str = None) -> Union[_T, DataList, DataDict]:
    """
    Converts lists into DataLists and dicts into DataDicts.
    """
    if isinstance(__object, dict):
        return DataDict(__object, parent, path=path)
    elif isinstance(__object, list):
        return DataList(__object, parent, path=path)
    return __object


class DataProvider:

    def __init__(self, data_path: str):
        self._data_path = data_path

        # maps all data elements (dicts, lists) onto their paths
        self._data_elements = {}

        # a lock for thread safety
        self._lock = Lock()

    def get_json_data(self, path_from_data_dir: str, default_value: Union[list, dict] = None):
        self._lock.acquire()

        # if element already exists, return that instead
        if path_from_data_dir in self._data_elements:
            self._lock.release()
            return self._data_elements[path_from_data_dir]

        # if it does not exist, it is created
        required_path = f"{self._data_path}/{path_from_data_dir}"
        if default_value is None:
            default_value = {}

        if not os.path.exists(required_path):
            os.makedirs(os.path.dirname(required_path), exist_ok=True)
            with open(required_path, "w") as f:
                json.dump(default_value, f)

        with open(required_path, "r") as f:
            content = json.load(f)
        data_element = convert(content, path=required_path)
        self._data_elements[path_from_data_dir] = data_element
        self._lock.release()
        return data_element
