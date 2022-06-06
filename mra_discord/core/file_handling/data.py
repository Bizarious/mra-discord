import os
from pathlib import Path
from threading import Lock
from typing import Union, Optional

from core.file_handling.savable import convert

_lock = Lock()
_data_path = None
_data_elements = {}


def maybe_convert_str_to_path(path: Union[str, Path]) -> Path:
    if type(path) == str:
        return Path(path)
    return path


def clear_data_elements():
    global _data_elements
    _data_elements = {}


class DataPathError(Exception):
    pass


def set_data_path(path: Union[str, Path]):
    path = maybe_convert_str_to_path(path)
    global _data_path
    if _data_path is not None:
        raise DataPathError("Data path can only be set once")
    _data_path = path


def get_json_data(path_from_data_dir: Union[str, Path], default_value: Optional[Union[list, dict]] = None):
    path_from_data_dir = maybe_convert_str_to_path(path_from_data_dir)
    if _data_path is None:
        raise DataPathError("Data path must be set")
    if path_from_data_dir.is_dir():
        raise FileNotFoundError(f"'{path_from_data_dir} must be a path to a file'")
    if not path_from_data_dir.name.endswith("json"):
        raise DataPathError("File ending must be .json")
    _lock.acquire()

    try:
        # if element already exists, return that instead
        if path_from_data_dir in _data_elements:
            data_element = _data_elements[path_from_data_dir]

        else:
            # if path (e.g. file or dirs) does not exist, it is created
            required_path = Path(f"{_data_path}/{path_from_data_dir}")
            default_value = default_value or {}
            if not required_path.exists():
                os.makedirs(os.path.dirname(required_path), exist_ok=True)

            # converts default data
            data_element = convert(default_value, path=required_path)
            _data_elements[path_from_data_dir] = data_element

    finally:
        _lock.release()
    return data_element
