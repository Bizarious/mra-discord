class TaskException(Exception):
    def __init__(self, arg=""):
        Exception.__init__(self, arg)


class UserHasNoTasksException(TaskException):
    def __init__(self, arg=""):
        TaskException.__init__(self, arg)


class TaskIdDoesNotExistException(TaskException):
    def __init__(self, arg=""):
        TaskException.__init__(self, arg)


class TaskCreationError(TaskException):
    def __init__(self, arg=""):
        TaskException.__init__(self, arg)
