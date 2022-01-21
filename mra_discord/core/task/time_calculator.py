from abc import ABC, abstractmethod
from datetime import datetime
from croniter import croniter
from typing import Type, Optional

import re


class TimeCalculator(ABC):
    """
    Base class for all time calculators.
    """

    def __init__(self):
        # overwrites context free function with the context one
        self.calculate_next_date = self._calculate_next_date_with_context

    @staticmethod
    @abstractmethod
    def calculate_next_date(date_str: str,
                            root_time: Optional[datetime] = datetime.now()
                            ) -> datetime:
        pass

    def _calculate_next_date_with_context(self,
                                          date_str: str,
                                          root_time: Optional[datetime] = datetime.now()
                                          ) -> datetime:
        return self.calculate_next_date(date_str, root_time)


class CronCalculator(TimeCalculator):
    """
    Calculates time after cron-like strings.
    """
    PATTERN = "(.+) (.+) (.+) (.+) (.+)"

    @staticmethod
    def calculate_next_date(date_string: str, root_time: Optional[datetime] = None) -> datetime:
        cron_iter = croniter(date_string, root_time)
        return cron_iter.get_next(datetime)


class FixedCalculator(TimeCalculator):
    """
    Calculates time after a fixed offset into the future.
    """
    PATTERN = ""

    def calculate_next_date(self, root_time: Optional[datetime] = None) -> datetime:
        pass


def choose_calculator(date_string: str) -> Type[TimeCalculator]:
    if re.search(CronCalculator.PATTERN, date_string) is not None:
        return CronCalculator
    elif re.search(FixedCalculator.PATTERN, date_string) is not None:
        return FixedCalculator
