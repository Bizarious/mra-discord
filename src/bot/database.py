import os
import json


class Data:
    path_data = "./data"
    path_config = "./data/config"

    def __init__(self):
        self.files_data = {"permissions": f"{self.path_data}/permissions.json",
                           "prefixes": f"{self.path_data}/prefixes.json"}
        self.files_config = {"tokens": f"{self.path_config}/tokens.json"}

        self.first_startup()

    def first_startup(self):
        if not os.path.exists(self.path_data):
            os.mkdir(self.path_data)
            print("created data directory")

        for k in self.files_data.keys():
            if not os.path.exists(self.files_data[k]):
                file = open(self.files_data[k], "w")
                json.dump({}, file)
                print(f"created {k}")

        if not os.path.exists(self.path_config):
            os.mkdir(self.path_config)
            print("created data directory")

        for k in self.files_config.keys():
            if not os.path.exists(self.files_config[k]):
                file = open(self.files_config[k], "w")
                json.dump({}, file)
                print(f"created {k}")

    def load(self, file):
        if file in self.files_data.keys():
            f = open(self.files_data[file])
            print(f"loaded {file}")
            return json.load(f)
        elif file in self.files_config.keys():
            f = open(self.files_config[file])
            print(f"loaded {file}")
            return json.load(f)

    def save(self, data, file):
        if file in self.files_data.keys():
            f = open(self.files_data[file], "w")
            json.dump(data, f)
            f.close()
            print(f"saved {file}")
        elif file in self.files_config.keys():
            f = open(self.files_config[file], "w")
            json.dump(data, f)
            f.close()
            print(f"saved {file}")
