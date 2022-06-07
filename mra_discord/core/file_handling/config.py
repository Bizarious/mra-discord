import os
from pathlib import Path
from threading import Lock
from typing import Optional, Dict, Union, Callable

from dotenv import dotenv_values

from core.file_handling.data import maybe_convert_str_to_path
from core.file_handling.savable import DataDict

_EXTERNAL_CATEGORY = "external"

_lock = Lock()
_config_path: Optional[Path] = None
_config_categories = {}


class ConfigPathError(Exception):
    pass


class ConfigCategoryError(Exception):
    pass


def clear_config_categories():
    global _config_categories
    _config_categories = {}


def set_config_path(path: Union[str, Path]) -> None:
    path = maybe_convert_str_to_path(path)
    global _config_path
    if _config_path is not None:
        raise ConfigPathError("Config path can only be set once")
    _config_path = path

    # if config path does not exist, it is created
    if not _config_path.exists():
        os.makedirs(_config_path, exist_ok=True)


class ConfigCategory:
    """ Contains all config settings belonging to one category. """

    def __init__(self, name: str, initial_values: Optional[Dict] = None, *, frozen: bool = False):
        self._name = name
        self._config_data = DataDict(initial_values, path=Path(f"{_config_path}/{name}.json"))
        self._frozen = frozen

    def get(self, key: str, *, default: Optional[str] = None) -> Optional[str]:
        return self._config_data.get(key, default)

    def set(self, key: str, value: Optional[str]):
        if self._frozen:
            raise ConfigCategoryError(f"The category '{self._name}' is frozen and therefore cannot be changed.")
        self._config_data[key] = value

    @classmethod
    def frozen(cls, name: str, initial_values: Optional[Dict] = None):
        return cls(name, initial_values, frozen=True)


def get_config_category(category: str) -> ConfigCategory:
    if _config_path is None:
        raise ConfigPathError("Config path must be set")

    _lock.acquire()
    try:
        if category not in _config_categories:
            category_object = ConfigCategory(category)
            _config_categories[category] = category_object
        else:
            category_object = _config_categories[category]
    finally:
        _lock.release()
    return category_object


class ExternalConfigImporter:
    """ Base class for importing config settings from external sources. """

    def __init__(self, path: Union[Path, str], extractor: Callable[[Path], Dict[str, str]]):
        self._path = maybe_convert_str_to_path(path)
        self._extractor = extractor

    def import_from_file(self) -> None:
        if _EXTERNAL_CATEGORY in _config_categories:
            raise ConfigCategoryError(f"Category '{_EXTERNAL_CATEGORY}' does already exist")

        raw_config_data = self._extractor(self._path)

        # converts all key to upper as a unified interface for all sources
        refined_config_data = {key.upper(): value for key, value in raw_config_data.items()}
        external = ConfigCategory.frozen(_EXTERNAL_CATEGORY, refined_config_data)
        _config_categories["external"] = external


class EnvConfigImporter(ExternalConfigImporter):
    """ Imports config settings from .env files. """

    def __init__(self, path: Union[Path, str]):
        ExternalConfigImporter.__init__(self, path, self.extract_env_data)

    @staticmethod
    def extract_env_data(path: Path) -> Dict[str, str]:
        return dotenv_values(path)


class JsonConfigImporter(ExternalConfigImporter):
    """ Imports config settings from .json files. """
    pass
