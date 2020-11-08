from croniter import croniter as cr
from datetime import datetime as dt, timedelta as td
from abc import ABC, abstractmethod
from copy import deepcopy
from core.enums import Dates
from core.task.task_exceptions import TaskCreationError


class Task(ABC):

    def __init__(self, *, author_id, channel_id=None, server_id=None, label=None):
        self.author_id = author_id
        self.channel_id = channel_id
        self.server_id = server_id
        self.label = label
        self._creation_time = dt.now()
        self._name = None
        self._kwargs = None

    @property
    def kwargs(self) -> dict:
        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs: dict):
        self._kwargs = kwargs

    @property
    def creation_time(self) -> dt:
        return self._creation_time

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def creation_time_string(self, format_string: str) -> str:
        return self._creation_time.strftime(format_string)

    @abstractmethod
    def to_json(self, format_string: str) -> dict:
        pass

    def from_json(self, kwargs: dict):
        self._creation_time = dt.strptime(kwargs["extra"]["creation_time"], Dates.DATE_FORMAT_DETAIL.value)
        self.name = kwargs["extra"]["type"]

    @abstractmethod
    def run(self):
        pass


class TimeBasedTask(Task, ABC):

    def __init__(self, *, author_id: int,
                 channel_id: int = None,
                 server_id: int = None,
                 date_string: str = "* * * * *",
                 label: str = None,
                 number: int = 0,
                 min_interval=0,
                 ):

        Task.__init__(self, author_id=author_id,
                      channel_id=channel_id,
                      server_id=server_id,
                      label=label
                      )

        self.time = []  # empty, if date string is not of form "* * * * *"
        self.date_string = date_string
        self.min_interval = min_interval

        if number == 0:
            self.counter = -1
        else:
            self.counter = number
        if " " not in date_string:
            self.counter = number
            for c in ["h", "m", "s"]:
                if date_string.count(c) > 1:
                    raise TaskCreationError(f"Multiple statements for '{c}' are not allowed")
            buffer = ""
            for c in date_string:
                buffer += c
                if c in ["h", "m", "s"]:
                    self.time.append(buffer)
                    buffer = ""

        self._next_time = deepcopy(self.creation_time)

        # flags
        self.delete = False

        self.get_next_date()

    def get_next_date(self) -> dt:
        if len(self.time) == 0:

            old_next_time = self.next_time
            dates = cr(self.date_string, self.next_time)
            self._next_time = dates.get_next(dt)
            while ((self._next_time - old_next_time).seconds / 60) < self.min_interval:
                self._next_time = dates.get_next(dt)

        else:

            hours = 0
            minutes = 0
            seconds = 0
            for time in self.time:
                if "h" in time:
                    hours = int(time[:-1])
                if "m" in time:
                    minutes = int(time[:-1])
                if "s" in time:
                    seconds = int(time[:-1])
            delta = td(hours=hours, minutes=minutes, seconds=seconds)
            self._next_time = dt.now().replace(microsecond=0) + delta

        return self.next_time

    @property
    def next_time(self) -> dt:
        return self._next_time

    def nex_time_string(self, format_string: str) -> str:
        return self._next_time.strftime(format_string)

    def calc_counter(self):
        if self.counter > 0:
            self.counter = self.counter - 1
        if self.counter == 0:
            self.delete = True

    def to_json(self, format_string: str) -> dict:
        return {"basic": self.kwargs,
                "extra": {"type": self.name,
                          "creation_time": self.creation_time_string(format_string),
                          "next_time": self.nex_time_string(Dates.DATE_FORMAT.value),
                          "delete": self.delete,
                          "label": self.label,
                          "counter": self.counter
                          }
                }

    def from_json(self, kwargs: dict):
        Task.from_json(self, kwargs)
        self._next_time = dt.strptime(kwargs["extra"]["next_time"], Dates.DATE_FORMAT.value)
        self.delete = kwargs["extra"]["delete"]
        self.counter = kwargs["extra"]["counter"]

    @abstractmethod
    def run(self):
        pass

    def execute(self):
        return self.run()


if __name__ == "__main__":
    t = TimeBasedTask(author_id=1, min_interval=10, date_string="*/10 * * * *")
    print(t.next_time)
    for _ in range(10):
        print(t.get_next_date())
