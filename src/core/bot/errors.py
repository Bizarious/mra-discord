class OnMessageCheckException(Exception):

    def __init__(self, arg):
        Exception.__init__(self, arg)


class CmdParserException(Exception):

    def __init__(self, arg):
        Exception.__init__(self, arg)
