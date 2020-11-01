class ConfigNotExistentError(Exception):
    def __init__(self, arg=""):
        Exception.__init__(self, arg)
