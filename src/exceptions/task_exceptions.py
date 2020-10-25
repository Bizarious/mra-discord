class TaskException(Exception):
    def __init__(self, arg):
        Exception.__init__(self, arg)


class UserHasNoTasks(TaskException):
    def __init__(self, arg):
        TaskException.__init__(self, arg)


class TaskIdDoesNotExist(TaskException):
    def __init__(self, arg):
        TaskException.__init__(self, arg)
