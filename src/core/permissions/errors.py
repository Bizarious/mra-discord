class GroupException(Exception):

    def __init__(self, arg):
        Exception.__init__(self, arg)


class GroupUserException(GroupException):
    def __init__(self, arg):
        GroupException.__init__(self, arg)
