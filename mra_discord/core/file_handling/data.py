import json
import os
from pathlib import Path
from threading import Lock
from typing import Union, Optional

from core.file_handling.savable import convert

_lock = Lock()
_data_path = None
_data_elements = {}


class DataPathError(Exception):
    pass


def set_data_path(path: Path):
    global _data_path
    if _data_path is not None:
        raise DataPathError("Data path can only be set once")
    _data_path = path


def get_json_data(path_from_data_dir: Path, default_value: Optional[Union[list, dict]] = None):
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
            # if it does not exist, it is created
            required_path = Path(f"{_data_path}/{path_from_data_dir}")
            if default_value is None:
                default_value = {}

            # if path (e.g. file or dirs) does not exist, it is created
            if not required_path.exists():
                os.makedirs(os.path.dirname(required_path), exist_ok=True)
                with open(required_path, "w") as f:
                    json.dump(default_value, f)

            # loads and converts data from file
            with open(required_path, "r") as f:
                content = json.load(f)
            data_element = convert(content, path=required_path)
            _data_elements[path_from_data_dir] = data_element

    finally:
        _lock.release()
    return data_element
