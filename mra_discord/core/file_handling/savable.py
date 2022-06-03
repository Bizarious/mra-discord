import json
from pathlib import Path
from threading import Lock
from typing import TypeVar, Union, Callable, Any, Optional, Dict, List

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class Savable:
    """
    Base class for savable objects. The idea is to create a custom container that saves its state
    to file as soon as it is changed, without the need to explicitly call a save function.
    """

    def __init__(self, parent=None, *, path: Path, indent: Optional[int] = None):
        if parent is None:
            self._parent = self
        else:
            self._parent = parent

        self._path = path

        # used to control if changes should be saved immediately
        self._do_save = True

        # a lock for thread safety
        self._lock = Lock()
        self._indent = indent

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

    def load(self) -> Optional[Union[Dict, List]]:
        # makes sure that e.g. a sublist will not load the original data leading into an endless recursion
        if self.parent is not self:
            data = None

        elif self._path.exists():
            # otherwise, if path exists, load it
            with open(self._path, "r") as file:
                data = json.load(file)

        else:
            data = None

        return data

    def save(self) -> None:
        if self._do_save:
            if self.parent is self:
                with open(self._path, "w") as file:
                    json.dump(self, file, indent=self._indent)
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
        # must be called at first, otherwise it cannot load data in the next step
        Savable.__init__(self, parent, path=path, indent=2)

        # tries to load existing data
        maybe_kwargs = self.load()

        if maybe_kwargs:
            # when data exists, take that
            actual_kwargs = maybe_kwargs
        else:
            # otherwise take data from constructor
            actual_kwargs = kwargs or dict()

        # converts all elements recursively to savables
        for key in actual_kwargs:
            actual_kwargs[key] = convert(actual_kwargs[key], path, self)

        dict.__init__(self, actual_kwargs)

    @_lock_and_save
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, convert(value, self._path, self))

    @_lock_and_save
    def pop(self, key: _KT) -> _VT:
        value = dict.pop(self, key)
        return value


class DataList(Savable, list):

    def __init__(self, seq: Optional[list] = None, *, parent: Savable = None, path: Path):
        # must be called at first, otherwise it cannot load data in the next step
        Savable.__init__(self, parent, path=path)

        # tries to load existing data
        maybe_seq = self.load()

        if maybe_seq:
            # when data exists, take that
            actual_seq = maybe_seq
        else:
            # otherwise take data from constructor
            actual_seq = seq or list()

        # converts all elements recursively to savables
        actual_seq = [convert(s, path, self) for s in actual_seq]

        list.__init__(self, actual_seq)

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
