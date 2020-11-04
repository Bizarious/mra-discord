import os
import json
from typing import Union


class DataBasic:
    path = ""

    def first_startup(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
            print(f"created {self.path} directory")


class Data(DataBasic):
    path = "./data"

    def __init__(self):

        self._buffer = {}
        self.first_startup()

    @property
    def buffer(self):
        return self._buffer

    @staticmethod
    def check_path(path: str):
        if not os.path.exists(path):
            os.mkdir(path)
            print(f"Created {path}")

    @staticmethod
    def check_file(file: str, path: str):
        if not os.path.exists(f"{path}/{file}"):
            f = open(f"{path}/{file}", "w")
            if file.endswith(".json"):
                json.dump({}, f)
            f.close()

    def _load_file(self, *, file: str, path: str = ""):
        path = f"{self.path}/{path}"
        self.check_path(path)
        self.check_file(file, path)
        return open(f"{path}/{file}")

    def get(self, *, file, path: str = "", buffer: bool = True) -> str:
        if file not in self._buffer.keys():
            f = self._load_file(file=file, path=path)
            content = f.read()
            if buffer:
                self._buffer[file] = content
            return content
        else:
            return self._buffer[file]

    def get_json(self, *, file, path: str = "", buffer: bool = True) -> Union[list, dict]:
        if file not in self._buffer.keys():
            f = self._load_file(file=file + ".json", path=path)
            content = json.load(f)
            if buffer:
                self._buffer[file] = content
            return content
        else:
            return self._buffer[file]

    def _save_file(self, *, data, file: str, path: str = ""):
        path = f"{self.path}/{path}"
        self.check_path(path)
        f = open(f"{path}/{file}", "w")
        if file.endswith(".json"):
            json.dump(data, f)
        else:
            f.write(data)
        f.close()

    def set(self, *, file, path: str = "", data, buffer: bool = True):
        if buffer:
            self._buffer[file] = data
        self._save_file(data=data, file=file, path=path)

    def set_json(self, *, file, path: str = "", data, buffer: bool = True):
        if buffer:
            self._buffer[file] = data
        self._save_file(data=data, file=file + ".json", path=path)


if __name__ == "__main__":
    d = Data()
    d.get_json(file="test", path="testing")
