from abc import ABC, abstractmethod
from datetime import datetime
from croniter import croniter
from typing import TYPE_CHECKING, Type, Optional

import re

if TYPE_CHECKING:
    from .task_base import TimeBasedTask


class TimeCalculator(ABC):
    """
    Base class for all time calculators.
    """

    def __init__(self, task: "TimeBasedTask"):
        self._task = task

    @abstractmethod
    def calculate_next_date(self, root_time: Optional[datetime] = None) -> datetime:
        pass


class CronCalculator(TimeCalculator):
    """
    Calculates time after cron-like strings.
    """
    PATTERN = "(.+) (.+) (.+) (.+) (.+)"

    def calculate_next_date(self, root_time: Optional[datetime] = None) -> datetime:
        if root_time is None:
            if self._task.next_time is None:
                root_time = datetime.now()
            else:
                root_time = self._task.next_time

        cron_iter = croniter(self._task.date_string, root_time)
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
