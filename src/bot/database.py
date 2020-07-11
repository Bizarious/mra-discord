import os
import json


class Data:

    def __init__(self):
        self.path = "./data"
        self.permissions_path = f'{self.path}/permissions.json'
        self.prefixes_path = f'{self.path}/prefixes.json'
        self.first_startup()

    def first_startup(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
            print("created data directory")
        # permissions
        if not os.path.exists(self.permissions_path):
            file = open(self.permissions_path, "w")
            json.dump({"users": [], "guilds": [], "channels": [], "blacklist": []}, file)
            file.close()
            print("created permissions file")
        if not os.path.exists(self.prefixes_path):
            file = open(self.prefixes_path, "w")
            json.dump({}, file)
            file.close()
            print("created prefixes file")

    def load_permissions(self):
        file = open(self.permissions_path)
        print("loaded permissions")
        return json.load(file)

    def save_permissions(self, permit):
        file = open(self.permissions_path, "w")
        json.dump(permit, file)
        file.close()
        print("saved permissions")

    def load_prefixes(self):
        file = open(self.prefixes_path)
        print("loaded prefixes")
        return json.load(file)

    def save_prefixes(self, prefix):
        file = open(self.prefixes_path, "w")
        json.dump(prefix, file)
        file.close()
        print("saved prefixes")
