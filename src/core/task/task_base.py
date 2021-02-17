import re
from typing import Union
from croniter import croniter as cr, CroniterBadCronError
from datetime import datetime as dt, timedelta as td
from abc import ABC, abstractmethod
from core.enums import Dates
from core.task.task_exceptions import TaskCreationError


class TimeCalculator(ABC):
    """
    The abstract class for the time calculator that is used by time-based tasks.
    """

    def __init__(self, date_string: str):
        self.date_string = date_string
        self.delete = False

    @abstractmethod
    def calculate_next_time(self, date_time: dt) -> dt:
        """
        Returns next date.
        """
        pass

    @abstractmethod
    def good_date_string(self) -> Union[None, str]:
        """
        Checks, if the passed date_string is good.
        """
        pass


class CronCalculator(TimeCalculator):
    """
    The cron-like calculator.
    """

    def __init__(self, date_string: str, min_interval: int = 0):
        TimeCalculator.__init__(self, date_string)
        self.min_interval = min_interval

    def calculate_next_time(self, date_time: dt) -> dt:
        it = cr(self.date_string, date_time)
        return it.get_next(dt)

    def good_date_string(self) -> Union[None, str]:
        try:
            it = cr(self.date_string, dt.now())
            a = it.get_next(dt)
            b = it.get_next(dt)
            if (b - a) < td(seconds=self.min_interval):
                return f"Date string falls below the min interval of {self.min_interval}s."
        except CroniterBadCronError:
            return "Bad date string"
        return None


class OffsetCalculator(TimeCalculator):
    """
    Uses "1h15m30s"-like strings.
    """

    def __init__(self, date_string: str):
        TimeCalculator.__init__(self, date_string)
        self.regex = "[1-9]+[0-9]*[h|m|s]"
        self.delete = True
        self.matches = self.calc_matches()

    def calc_matches(self):
        return re.findall(self.regex, self.date_string)

    def calculate_next_time(self, date_time: dt) -> dt:
        for time in self.matches:
            if time[-1] == "h":
                date_time += td(hours=int(time[:-1]))
            elif time[-1] == "m":
                date_time += td(minutes=int(time[:-1]))
            elif time[-1] == "s":
                date_time += td(seconds=int(time[:-1]))
        return date_time.replace(microsecond=0)

    def good_date_string(self) -> Union[None, str]:
        return None


class AbstractDateStringParser(ABC):
    """
    The abstract class for the datestring-parser.
    """

    # the regex that is used to differ the time calculators
    regex: [str] = []

    @abstractmethod
    def parse(self, date_string: str, min_interval: int) -> TimeCalculator:
        pass


class DefaultDateStringParser(AbstractDateStringParser):
    """
    The default implementation of the datestring-parser. Chooses between cron-like and implicit calculator.
    """

    regex = ["[1-9]+[0-9]*[h|m|s]"]

    def parse(self, date_string: str, min_interval: int) -> TimeCalculator:
        if re.findall(self.regex[0], date_string):
            return OffsetCalculator(date_string)
        else:
            return CronCalculator(date_string, min_interval)


class Task(ABC):
    """
    Abstract class for tasks in general.
    """

    def __init__(self, *, author_id, channel_id=None, server_id=None, label=None):
        self.author_id = author_id
        self.channel_id = channel_id
        self.server_id = server_id
        self.label = label
        self._creation_time = dt.now()
        self._name = None   # the type of task
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

    @creation_time.setter
    def creation_time(self, time: dt):
        self._creation_time = time

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def creation_time_string(self, format_string: str) -> str:
        return self._creation_time.strftime(format_string)

    def to_json(self, format_string: str) -> dict:
        d = {"arguments": self.kwargs,
             "extra": {"creation_time": self.creation_time_string(format_string),
                       "type": self.name}}

        return d

    def from_json(self, kwargs: dict):
        self.creation_time = dt.strptime(kwargs["creation_time"], Dates.DATE_FORMAT_DETAIL.value)
        self.name = kwargs["type"]

    @abstractmethod
    def run(self):
        pass


class TimeBasedTask(Task, ABC):

    def __init__(self, *, date_string="* * * * *",
                 dsp=DefaultDateStringParser(),
                 author_id,
                 channel_id=None,
                 server_id=None,
                 label=None,
                 min_interval=0
                 ):

        Task.__init__(self, author_id=author_id, channel_id=channel_id, server_id=server_id, label=label)

        self.time_calc: TimeCalculator = dsp.parse(date_string, min_interval)
        check = self.time_calc.good_date_string()
        if check is not None:
            raise TaskCreationError(check)

        self._next_date: dt = dt.now()

    def __lt__(self, other):
        # this task is earlier than the other
        if self.next_date < other.next_date:
            return True
        # both have same date
        elif self.next_date == other.next_date:
            # check for creation time
            if self.creation_time < other.creation_time:
                return True
        return False

    @property
    def next_date(self):
        return self._next_date

    @next_date.setter
    def next_date(self, next_date: dt):
        self._next_date = next_date

    @property
    def delete(self):
        return self.time_calc.delete

    def next_date_string(self):
        return self.next_date.strftime(Dates.DATE_FORMAT.value)

    def calc_next_date(self) -> dt:
        return self.time_calc.calculate_next_time(self.next_date)

    @abstractmethod
    def run(self):
        pass

    def to_json(self, format_string: str) -> dict:
        d = Task.to_json(self, format_string)
        d["extra"]["next_date"] = self.next_date_string()
        d["extra"]["delete"] = self.delete

        return d

    def from_json(self, kwargs: dict):
        Task.from_json(self, kwargs)
        self.next_date = dt.strptime(kwargs["next_date"], Dates.DATE_FORMAT.value)


if __name__ == "__main__":
    o = CronCalculator("20 19 * * *", 60)
    print(o.good_date_string())
