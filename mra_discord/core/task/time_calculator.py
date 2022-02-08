from abc import ABC, abstractmethod
from datetime import datetime
from croniter import croniter
from typing import Type, Optional

import re


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
                                         ) -> datetime:
        return self.calculate_next_date(date_str, root_time)


class CronCalculator(TimeCalculator):
    """
    Calculates time after cron-like strings.
    """
    @staticmethod
    def calculate_next_date(date_string: str, root_time: Optional[datetime] = None) -> datetime:
        cron_iter = croniter(date_string, root_time)
        return cron_iter.get_next(datetime)


class FixedCalculator(TimeCalculator):
    """
    Calculates time after a fixed offset into the future.
    """
    def calculate_next_date(self, root_time: Optional[datetime] = None) -> datetime:
        pass


_CALCULATOR_MAPPING = {
    "(.+) (.+) (.+) (.+) (.+) (.+)": CronCalculator,
    "": FixedCalculator
}


def choose_calculator(date_string: str) -> Optional[Type[TimeCalculator]]:
    for pattern, calculator in _CALCULATOR_MAPPING.items():
        if re.search(pattern, date_string) is not None:
            return calculator
    return None
