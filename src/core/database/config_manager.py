import os
from core.database import DataBasic
from core.database.errors import ConfigNotExistentError
from typing import Union


class ConfigManager(DataBasic):

    path = "./config"
    config_file = "config.txt"
    tokens_file = "tokens.txt"
    config_file_path = f"{path}/config.txt"
    tokens_file_path = f"{path}/tokens.txt"

    def __init__(self):
        self.configs = {}
        self.tokens = {}
        self.first_startup()
        self._load_configs()
        self._load_tokens()

    def first_startup(self):
        DataBasic.first_startup(self)
        if not os.path.exists(self.config_file_path):
            f = open(self.config_file_path, "w")
            f.write("")
            f.close()
            print("Config File created")
        if not os.path.exists(self.tokens_file_path):
            f = open(self.tokens_file_path, "w")
            f.write("")
            f.close()
            print("Tokens File created")

    def _load_configs(self):
        f = open(self.config_file_path)
        lines = f.readlines()
        for s in lines:
            if "\n" in s:
                s = s[:-1]
            s = s.split("=")
            self.configs[s[0]] = s[1]

    def _save_configs(self):
        lines = []
        for k in self.configs.keys():
            lines.append(f"{k}={self.configs[k]}\n")

        f = open(self.config_file_path, "w")
        f.writelines(lines)
        f.close()

    def _load_tokens(self):
        f = open(self.tokens_file_path)
        lines = f.readlines()
        for s in lines:
            if "\n" in s:
                s = s[:-1]
            s = s.split("=")
            self.tokens[s[0]] = s[1]

    def _save_tokens(self):
        lines = []
        for k in self.tokens.keys():
            lines.append(f"{k}={self.tokens[k]}\n")

        f = open(self.tokens_file_path, "w")
        f.writelines(lines)
        f.close()

    def get_config(self, name: str) -> Union[str, None]:
        if name in self.configs.keys():
            return self.configs[name]
        return None

    def set_config(self, name: str, value: str):
        if name not in self.configs.keys():
            raise ConfigNotExistentError("You cannot change a non existent config. "
                                         "Run 'set_default_config to apply a default value'")
        self.configs[name] = value
        self._save_configs()

    def get_token(self, name: str) -> Union[str, None]:
        if name in self.tokens.keys():
            return self.tokens[name]
        return None

    def set_token(self, name: str, value: str):
        self.tokens[name] = value
        self._save_tokens()

    def set_default_config(self, name: str, value: str):
        if name not in self.configs.keys():
            self.configs[name] = value
        self._save_configs()


if __name__ == "__main__":
    c = ConfigManager()
    print(c.get_config("test1"))
    print(c.get_token("bot"))
    print(c.configs)
    print(c.tokens)
