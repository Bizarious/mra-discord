from croniter import croniter as cr
from datetime import datetime as dt
from abc import ABC, abstractmethod


class Task(ABC):
    date_format = "%d.%m.%y %H:%M"

    def __init__(self, *, creation_time=None):
        if creation_time is None:
            self.creation_time = dt.now().replace(microsecond=0)
        else:
            self.creation_time = dt.strptime(creation_time, self.date_format)

    @abstractmethod
    def run(self):
        pass


class TimeBasedTask(Task, ABC):

    def __init__(self, *, minutes="*", hours="*", days="*", months="*", weekdays="*", creation_time=None):
        Task.__init__(self, creation_time=creation_time)
        self.minutes = minutes
        self.hours = hours
        self.days = days
        self.months = months
        self.weekdays = weekdays

        self.delete = False

    def get_next_date(self):
        dates = cr(f"{self.minutes} {self.hours} {self.days} {self.months} {self.weekdays}", dt.now())
        return dates.get_next(dt)

    def run(self):
        pass


if __name__ == "__main__":
    t = TimeBasedTask(minutes="*/5", hours="12", days="15", creation_time="19.12.45 14:08")
    print(t.get_next_date())
    print(t.creation_time)
