import re
from croniter import croniter as cr, CroniterBadCronError
from datetime import datetime as dt, timedelta as td
from abc import ABC, abstractmethod
from copy import deepcopy
from core.enums import Dates
from core.task.task_exceptions import TaskCreationError


class TimeCalculator(ABC):
    """
    The abstract class for the time calculator that is used by time-based tasks.
    """

    def __init__(self, date_string):
        self.date_string = date_string

    @abstractmethod
    def calculate_next_time(self, date_time: dt) -> dt:
        pass

    @abstractmethod
    def good_date_string(self) -> bool:
        pass


class CronCalculator(TimeCalculator):
    """
    The cron-like calculator.
    """

    def calculate_next_time(self, date_time: dt) -> dt:
        it = cr(self.date_string, date_time)
        return it.get_next(dt)

    def good_date_string(self) -> bool:
        try:
            it = cr(self.date_string, dt.now())
        except CroniterBadCronError:
            return False
        return True


class ImplicitCalculator(TimeCalculator):
    """
    Uses "1h15m30s"-like strings.
    """

    def calculate_next_time(self, date_time: dt) -> dt:
        """
        Returns next date.
        """
        pass

    def good_date_string(self) -> bool:
        """
        Checks, if the passed date_string is good.
        """
        pass


class AbstractDateStringParser(ABC):
    """
    The abstract class for the datestring-parser.
    """

    # the regex that is used to differ the time calculators
    regex: [str] = []

    @abstractmethod
    def parse(self, date_string: str) -> TimeCalculator:
        pass


class DefaultDateStringParser(AbstractDateStringParser):
    """
    The default implementation of the datestring-parser. Chooses between cron-like and implicit calculator.
    """

    regex = ["[1-9]+[0-9]*[h|m|s]"]

    def parse(self, date_string: str) -> TimeCalculator:
        if re.findall(self.regex[0], date_string):
            return ImplicitCalculator(date_string)
        else:
            return CronCalculator(date_string)


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

    def __init__(self, *, date_string="* * * * *",
                 dsp=DefaultDateStringParser(),
                 author_id,
                 channel_id=None,
                 server_id=None,
                 label=None
                 ):

        Task.__init__(self, author_id=author_id, channel_id=channel_id, server_id=server_id, label=label)

        self.time_calc: TimeCalculator = dsp.parse(date_string)
        if not self.time_calc.good_date_string():
            raise TaskCreationError("Bad date string")

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

    def calc_next_date(self) -> dt:
        return self.time_calc.calculate_next_time(self.next_date)

    @abstractmethod
    def run(self):
        pass

    def to_json(self, format_string: str) -> dict:
        pass


if __name__ == "__main__":
    t = TimeBasedTask(date_string="5 20 * * * */5", author_id=0)
    for _ in range(5):
        t.next_date = t.calc_next_date()
        print(t.next_date)
