import os
from typing import Union
from core.database import DataBasic
from core.database.errors import ConfigNotExistentError
from configparser import ConfigParser


class ConfigManager(DataBasic):

    path = "./config"
    config_file_path = f"{path}/config.ini"

    def __init__(self):
        self.configs = ConfigParser()
        self.tokens = {}
        self.first_startup()
        self._load_configs()
        self._check_integrity()

    def first_startup(self):
        DataBasic.first_startup(self)
        if not os.path.exists(self.config_file_path):
            self.configs["Tokens"] = {}
            self._save_configs()
            print("Config File created")

    def _load_configs(self):
        self.configs.read(self.config_file_path)

    def _save_configs(self):
        with open(self.config_file_path, "w") as file:
            self.configs.write(file)

    def _check_integrity(self):
        if "Tokens" not in self.configs:
            self.configs["Tokens"] = {}
            self._save_configs()

    def get_config(self, name: str, section: str) -> Union[str, None]:
        if section in self.configs and name in self.configs[section]:
            return self.configs[section][name]
        return None

    def set_config(self, name: str, section: str, value: str):
        if section not in self.configs:
            raise ConfigNotExistentError("This section does not exist. "
                                         "Run 'set_default_config to apply a default value'")
        if name not in self.configs[section]:
            raise ConfigNotExistentError("You cannot change a non existent config. "
                                         "Run 'set_default_config to apply a default value'")
        self.configs[section][name] = value
        self._save_configs()

    def get_token(self, name: str) -> Union[str, None]:
        return self.get_config(name, "Tokens")

    def set_token(self, name: str, value: str):
        self.configs["Tokens"][name] = value
        self._save_configs()

    def set_default_config(self, name: str, section: str, value: str):
        changed = False
        if section not in self.configs:
            self.configs[section] = {}
            changed = True
        if name not in self.configs[section]:
            self.configs[section][name] = value
            changed = True
        if changed:
            self._save_configs()
