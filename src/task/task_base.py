from abc import ABC, abstractmethod


class Task(ABC):
    date_format = "%d.%m.%y %H:%M"

    def __init__(self):
        pass


class TimeBasedTask(Task, ABC):

    def __init__(self):
        Task.__init__(self)
