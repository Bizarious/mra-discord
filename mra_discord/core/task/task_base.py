from typing import Optional


class TaskPackage:

    def __init__(self, name: str, task_class: "Task"):
        self._name = name
        self._task_class = task_class

    @property
    def name(self):
        return self._name

    @property
    def task_class(self):
        return self._task_class


def task(name: Optional[str] = None):
    def dec(cls):
        if name is None:
            return TaskPackage(cls.__name__, cls)
        return TaskPackage(name, cls)
    return dec


class Task:

    def __init__(self):
        pass


class TimeBasedTask(Task):

    def __init__(self, *, date_string):
        Task.__init__(self)

        self._date_string = date_string
        self._next_time = None

    @property
    def date_string(self):
        return self._date_string

    @property
    def next_time(self):
        return self._next_time
