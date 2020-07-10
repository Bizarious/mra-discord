import os
import json


class Data:

    def __init__(self):
        self.path = "./data"
        self.permissions_path = f'{self.path}/permissions.json'
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

    def load_permissions(self):
        file = open(self.permissions_path)
        print("loaded permissions")
        return json.load(file)

    def save_permissions(self, permit):
        file = open(self.permissions_path, "w")
        json.dump(permit, file)
        file.close()
        print("saved permissions")
