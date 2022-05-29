import json
from pathlib import Path
from threading import Lock
from typing import TypeVar, Union, Callable, Any, Optional

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class Savable:
    """
    Base class for savable objects. The idea is to create a custom container that saves its state
    to file as soon as it is changed, without the need to explicitly call a save function.
    """

    def __init__(self, parent=None, *, path: Path):
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
    def parent(self) -> "Savable":
        return self._parent

    @property
    def path(self) -> Path:
        return self._path

    @property
    def do_save(self) -> bool:
        return self._do_save

    @property
    def lock(self) -> Lock:
        return self._lock

    @do_save.setter
    def do_save(self, save: bool) -> None:
        self._do_save = save
        if save:
            self.save()

    def save(self) -> None:
        if self._do_save:
            if self.parent == self:
                with open(self._path, "w") as file:
                    json.dump(self, file, indent=0)
            else:
                self.parent.save()


def _lock_and_save(func: Callable[[Savable, ...], Any]) -> Callable[[Savable, ...], Any]:
    def lock_and_save0(savable: Savable, *args, **kwargs) -> Any:
        savable.lock.acquire()
        try:
            maybe_return = func(savable, *args, **kwargs)
            savable.save()
        finally:
            savable.lock.release()
        return maybe_return
    return lock_and_save0


class DataDict(Savable, dict):

    def __init__(self, kwargs: Optional[dict] = None, *, parent: Optional[Savable] = None, path: Path):
        # converts all elements recursively to savables
        kwargs = kwargs or dict()
        for key in kwargs:
            kwargs[key] = convert(kwargs[key], path, self)

        dict.__init__(self, kwargs)
        Savable.__init__(self, parent, path=path)

    @_lock_and_save
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, convert(value, self._path, self))

    @_lock_and_save
    def pop(self, key: _KT) -> _VT:
        value = dict.pop(self, key)
        return value


class DataList(Savable, list):

    def __init__(self, seq: Optional[list] = None, *, parent: Savable = None, path: Path):
        # converts all elements recursively to data lists and data dicts
        seq = seq or list()
        seq = [convert(s, path, self) for s in seq]

        list.__init__(self, seq)
        Savable.__init__(self, parent, path=path)

    @_lock_and_save
    def append(self, __object: _T) -> None:
        list.append(self, convert(__object, self._path, self))

    @_lock_and_save
    def remove(self, __value: _T) -> None:
        list.remove(self, __value)

    @_lock_and_save
    def pop(self, __index: int = ...) -> _T:
        element = list.pop(self, __index)
        return element


_CONVERSION_TABLE = {
    dict: DataDict,
    list: DataList,
}


def convert(__object: _T, path: Path, parent: Savable = None) -> Union[_T, DataList, DataDict]:
    """
    Converts lists into DataLists and dicts into DataDicts.
    """
    maybe_convert_into = _CONVERSION_TABLE.get(type(__object))
    if maybe_convert_into is not None:
        converted_object = maybe_convert_into(__object, parent=parent, path=path)
    else:
        converted_object = __object
    return converted_object
