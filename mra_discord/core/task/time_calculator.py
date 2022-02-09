import re

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from croniter import croniter
from typing import Type, Optional


class TimeCalculator(ABC):
    """
    Base class for all time calculators.
    """
    @staticmethod
    @abstractmethod
    def calculate_next_date(date_str: str,
                            root_time: datetime = datetime.now()
                            ) -> datetime:
        pass

    def calculate_next_date_with_context(self,
                                         date_str: str,
                                         root_time: datetime = datetime.now()
                                         ) -> Optional[datetime]:
        return self.calculate_next_date(date_str, root_time)


class CronCalculator(TimeCalculator):
    """
    Calculates time after cron-like strings.
    """
    @staticmethod
    def calculate_next_date(date_string: str, root_time: Optional[datetime] = None) -> datetime:
        cron_iter = croniter(date_string, root_time)
        return cron_iter.get_next(datetime)


class FixedOffsetCalculator(TimeCalculator):
    """
    Calculates time after a fixed offset into the future.
    """

    def __init__(self):
        self._delete = False

    @staticmethod
    def calculate_next_date(date_str: str,
                            root_time: datetime = datetime.now().replace(microsecond=0)
                            ) -> datetime:

        time_add = {}

        for i, unit in enumerate(date_str):
            if unit in ["d", "h", "m", "s"]:
                if unit in time_add:
                    raise KeyError(f"'{unit}' is only allowed once")
                time_add[unit] = int(date_str[i-1])

        return root_time + timedelta(
            days=time_add.get("d", 0),
            hours=time_add.get("h", 0),
            minutes=time_add.get("m", 0),
            seconds=time_add.get("s", 0),
        )

    def calculate_next_date_with_context(self,
                                         date_str: str,
                                         root_time: datetime = datetime.now()
                                         ) -> Optional[datetime]:
        if self._delete:
            return None
        self._delete = True
        return self.calculate_next_date(date_str, root_time)


_CALCULATOR_MAPPING = {
    "^(.+) (.+) (.+) (.+) (.+) (.+)$": CronCalculator,
    "^([1-9]{1,}[d,h,s,m]){1,4}$": FixedOffsetCalculator
}


def choose_calculator(date_string: str) -> Optional[Type[TimeCalculator]]:
    for pattern, calculator in _CALCULATOR_MAPPING.items():
        if re.search(pattern, date_string) is not None:
            return calculator
    return None


if __name__ == "__main__":
    print(choose_calculator(""))
