from abc import ABC, abstractmethod
from datetime import datetime as dt, timedelta as td


class Task(ABC):
    savable = True
    date_format = "%d.%m.%y %H:%M"
    mode = None  # bot/core

    def __init__(self):
        self._creation_time = dt.now().strftime(self.date_format)
        self._id = 0
        self._ctx = None
        self._type = None  # type of task, e.g. "Reminder"
        self._final = False

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, mode):
        self._type = mode

    @property
    def final(self):  # delete after execution?
        return self._final

    @abstractmethod
    def execute(self):
        pass

    @property
    def ctx(self):
        return self._ctx

    @ctx.setter
    def ctx(self, ctx):
        self._ctx = ctx

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, idc):
        self._id = idc


class TimeBasedTask(Task, ABC):

    def __init__(self, *, minutes="*", hours="*", days="*", months="*", years="*", week_days="*"):

        super().__init__()
        self._next_time = self.time_now
        times = {"minutes": minutes, "hours": hours, "days": days,
                 "months": months, "years": years, "week_days": week_days}
        for key in times.keys():
            time = times[key]
            if "," in time:
                time = time.split(",")
                time = [int(i) for i in time]
            elif "/" in time:
                time = time.split("/")
                buffer = time[0].split("-")
                if len(buffer) == 1:
                    raise RuntimeError("left single argument not allowed when '/' is used.\n   Expected: '0-10'")
                else:
                    time = range(int(buffer[0]), int(buffer[1]) + 1, int(time[1]))
            elif "-" in time and "/" not in time:
                time = time.split("-")
                time = range(int(time[0]), int(time[1]) + 1)
            else:
                if "*" in time:
                    time = ["*"]
                else:
                    time = [int(time)]
            times[key] = time

        self.minutes = times["minutes"]
        self.hours = times["hours"]
        self.days = times["days"]
        self.months = times["months"]
        self.years = times["years"]
        self.week_days = times["week_days"]

        self.final_time = self.calc_final()
        if self.final_time < self.time_now:
            raise RuntimeError("target time must not be in the past")

        self.set_next_target_time()

    def calc_final(self):
        if "*" in self.years:
            return False
        else:
            year = self.years[-1]
        if "*" in self.months:
            month = 12
        else:
            month = self.months[-1]
        if "*" in self.days:
            day = 31
        else:
            day = self.days[-1]
        if "*" not in self.week_days:
            week_day = self.week_days
        else:
            week_day = [1, 2, 3, 4, 5, 6, 7]
        if "*" in self.hours:
            hour = 23
        else:
            hour = self.hours[-1]
        if "*" in self.minutes:
            minute = 59
        else:
            minute = self.minutes[-1]
        d = dt(year=year, month=month, day=day, hour=hour, minute=minute)
        tide = td(days=1)
        while d.isoweekday() not in week_day:
            d -= tide
        return d

    @property
    def final(self):
        return self._next_time == self.final_time

    def set_next_target_time(self):
        delta = td(minutes=1)
        time = self.target_time
        while time < self.time_now or not self.is_in_interval(time):
            time += delta
        self._next_time = time

    def is_in_interval(self, time: dt):
        if (time.minute in self.minutes or "*" in self.minutes) \
                and (time.hour in self.hours or "*" in self.hours) \
                and (time.day in self.days or "*" in self.days) \
                and (time.month in self.months or "*" in self.months) \
                and (time.year in self.years or "*" in self.years) \
                and (time.isoweekday() in self.week_days or "*" in self.week_days):
            return True
        return False

    @property
    def time_now(self):
        return dt.now().replace(second=0, microsecond=0)

    @property
    def target_time(self):
        return self._next_time


if __name__ == "__main__":
    t = TimeBasedTask(years="2020", months="6", days="3", hours="0", minutes="12")
    print(t.final)
