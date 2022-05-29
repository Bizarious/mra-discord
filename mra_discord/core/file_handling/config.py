import os
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Optional, Dict

from dotenv import dotenv_values

from core.file_handling.savable import DataDict

_lock = Lock()
_config_path: Optional[Path] = None
_config_categories = {}


class ConfigPathError(Exception):
    pass


class ConfigCategoryError(Exception):
    pass


def set_config_path(path: Path):
    global _config_path
    if _config_path is not None:
        raise ConfigPathError("Data path can only be set once")
    _config_path = path

    # if config path does not exist, it is created
    if not _config_path.exists():
        os.makedirs(_config_path, exist_ok=True)


class _ConfigCategory:
    """ Contains all config settings belonging to one category. """

    def __init__(self, name: str):
        self._name = name
        self._config_data = DataDict(path=Path(f"{_config_path}/{name}.json"))
        self._frozen = False

    def get(self, key: str, *, default: Optional[str] = None) -> Optional[str]:
        if key not in self._config_data:
            if self._frozen:
                raise ConfigCategoryError(
                    f"Please specify an existing key. "
                    f"The category '{self._name}' is frozen and therefore cannot be changed."
                )
            else:
                self._config_data[key] = default
                return default
        else:
            return self._config_data[key]

    def set(self, key: str, value: Optional[str]):
        if self._frozen:
            raise ConfigCategoryError(f"The category '{self._name}' is frozen and therefore cannot be changed.")
        self._config_data[key] = value

    def freeze(self):
        """ Freezes the config category so that config values cannot be changed anymore """
        self._frozen = True


def get_config_category(category: str) -> _ConfigCategory:
    if _config_path is None:
        raise ConfigPathError("Config path must be set")

    _lock.acquire()
    try:
        if category not in _config_categories:
            category_object = _ConfigCategory(category)
            _config_categories[category] = category_object
        else:
            category_object = _config_categories[category]
    finally:
        _lock.release()
    return category_object


class ExternalConfigImporter(ABC):
    """ Base class for importing config settings from external sources. """

    def __init__(self):
        self._external_category = get_config_category("external")

    @abstractmethod
    def extract_config_values(self, file: Path) -> Dict[str, str]:
        config = dotenv_values(file)

    def import_from_file(self, file: Path):
        pass


class EnvConfigImporter(ExternalConfigImporter):
    """ Imports config settings from .env files. """
    pass


class JsonConfigImporter(ExternalConfigImporter):
    """ Imports config settings from .json files. """
    pass
