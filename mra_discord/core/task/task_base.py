from datetime import datetime
from typing import Optional, Type, Any

from core.task.time_calculator import choose_calculator


FIELD_DATE_STRING = "date_string"
FIELD_NEXT_TIME = "next_time"
FIELD_OWNER = "owner"
FIELD_SOURCE = "source"
FIELD_CHANNEL = "channel"


class TaskPackage:

    def __init__(self, name: str, task_class: Type["TimeBasedTask"]):
        self._name = name
        self._task_class = task_class

    @property
    def name(self):
        return self._name

    @property
    def task_class(self):
        return self._task_class


def task(name: Optional[str] = None):
    def dec(cls):
        if name is None:
            return TaskPackage(cls.__name__, cls)
        return TaskPackage(name, cls)
    return dec


class TaskFields:

    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def raw_dict(self):
        return self._raw_dict

    def get(self, key: str, default: Any = None, required: bool = False):
        if required:
            if key not in self._raw_dict.keys():
                raise KeyError(f"The field '{key}' is required")
        return self._raw_dict.get(key, default)


class TimeBasedTask:

    def __init__(self, fields: TaskFields):
        self._date_string = fields.get(FIELD_DATE_STRING, required=True)
        self._owner = fields.get(FIELD_OWNER, required=True)
        self._source = fields.get(FIELD_SOURCE, required=True)
        self._next_time = fields.get(FIELD_NEXT_TIME)
        self._channel = fields.get(FIELD_CHANNEL)

        self._calculator = choose_calculator(self._date_string)()

    @property
    def date_string(self) -> str:
        return self._date_string

    @property
    def next_time(self) -> Optional[datetime]:
        return self._next_time

    @property
    def source(self) -> str:
        return self._source

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def channel(self) -> int:
        return self._channel

    def set_next_time(self, time: Optional[datetime] = None):
        if time is None:
            if self._next_time is None:
                time = datetime.now()
            else:
                time = self._next_time
        self._next_time = self._calculator.calculate_next_date_with_context(self._date_string, time)

    def run(self) -> Optional[tuple[str, Any]]:
        pass

    def execute(self):
        return self.run()
