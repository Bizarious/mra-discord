class Data:

    def __init__(self):
        self.path = "./data"

    def load(self, path, mode):
        with open(f'{self.path}/{path}', mode) as file:
            return file

    def save(self, file, path):
        pass
