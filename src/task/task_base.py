from croniter import croniter as cr
from datetime import datetime as dt, timedelta as td
from abc import ABC, abstractmethod
from enums import Dates


class Task(ABC):

    def __init__(self, *, author_id, channel_id=None, server_id=None):
        self.author_id = author_id
        self.channel_id = channel_id
        self.server_id = server_id
        self._creation_time = dt.now()
        self._name = None

    @property
    def creation_time(self):
        return self._creation_time

    @property
    def creation_time_string(self):
        return self._creation_time.strftime(Dates.DATE_FORMAT.value)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @abstractmethod
    def to_json(self) -> dict:
        pass

    def from_json(self, kwargs: dict):
        self._creation_time = dt.strptime(kwargs["extra"]["creation_time"], Dates.DATE_FORMAT.value)
        self.name = kwargs["extra"]["type"]

    @abstractmethod
    def run(self):
        pass


class TimeBasedTask(Task, ABC):

    def __init__(self, *, author_id,
                 channel_id=None,
                 server_id=None,
                 date_string="* * * * *"):
        Task.__init__(self, author_id=author_id,
                      channel_id=channel_id,
                      server_id=server_id)

        self.time = []
        self.date_string = date_string
        if " " not in date_string:
            buffer = ""
            for c in date_string:
                buffer += c
                if c in ["h", "m", "s"]:
                    self.time.append(buffer)
                    buffer = ""

        self._next_time = None
        self.get_next_date()

        # flags
        self.delete = False

    def get_next_date(self):
        if len(self.time) == 0:
            dates = cr(self.date_string, dt.now())
            self._next_time = dates.get_next(dt)
        else:
            self.delete = True
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
        return self._next_time

    @property
    def next_time(self):
        return self._next_time

    @property
    def nex_time_string(self):
        return self._next_time.strftime(Dates.DATE_FORMAT.value)

    def to_json(self) -> dict:
        return {"basic": {"date_string": self.date_string,
                          "author_id": self.author_id,
                          "channel_id": self.channel_id,
                          "server_id": self.server_id,
                          },
                "extra": {"type": self.name,
                          "creation_time": self.creation_time_string,
                          "next_time": self.nex_time_string,
                          "delete": self.delete
                          }
                }

    def from_json(self, kwargs):
        Task.from_json(self, kwargs)
        self._next_time = dt.strptime(kwargs["extra"]["next_time"], Dates.DATE_FORMAT.value)
        self.delete = kwargs["extra"]["delete"]

    @abstractmethod
    def run(self):
        pass


if __name__ == "__main__":
    t = TimeBasedTask(author_id=1)
    print(t.get_next_date())
