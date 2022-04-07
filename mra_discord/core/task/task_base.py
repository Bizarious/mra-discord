from datetime import datetime
from typing import Optional, Type, Any, Callable, Union

from core.task.time_calculator import choose_calculator
from core.ext.modules import ipc

TASK_FIELD_DATE_STRING = "Date string"
TASK_FIELD_NEXT_TIME = "Next time"
TASK_FIELD_SOURCE = "source"
TASK_FIELD_ID = "id"
TASK_FIELD_OWNER = ipc.CONTENT_FIELD_AUTHOR
TASK_FIELD_CHANNEL = "Channel"
TASK_FIELD_TYPE = "Type"

DATE_CONVERTER = "%d.%m.%Y %H:%M:%S"


class TaskPackage:

    def __init__(
            self,
            name: str,
            task_class: Type["TimeBasedTask"],
            fields_checker: Callable[["TaskFields"], "TaskFields"]
    ):
        self._name = name
        self._task_class = task_class
        self._fields_checker = fields_checker

        self._checks = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def task_class(self) -> Type["TimeBasedTask"]:
        return self._task_class

    @property
    def fields_checker(self) -> Callable[["TaskFields"], "TaskFields"]:
        def fields_checker0(fields: "TaskFields") -> "TaskFields":
            fields = _base_fields_checker(fields)
            return self._fields_checker(fields)
        return fields_checker0


def task(
        name: Optional[str] = None,
        fields_checker: Callable[["TaskFields"], "TaskFields"] = lambda t: t
) -> Callable[[Type["TimeBasedTask"]], TaskPackage]:

    def dec(cls):
        if name is None:
            return TaskPackage(cls.__name__, cls, fields_checker)
        return TaskPackage(name, cls, fields_checker)

    return dec


class TaskFields:

    def __init__(self, raw_dict: dict):
        self._raw_dict = raw_dict

    @property
    def raw_dict(self):
        return self._raw_dict

    def get(self, key: str):
        return self._raw_dict.get(key)

    def set(self, key: str, value: Union[str, int]):
        self._raw_dict[key] = value

    def check_and_set(self, key: str, default: Optional[Union[str, int]] = None, required: bool = False):
        if key not in self._raw_dict.keys():
            if required:
                raise KeyError(f"The field '{key}' is required")
            self._raw_dict[key] = default


def _base_fields_checker(fields: TaskFields):
    fields.check_and_set(TASK_FIELD_DATE_STRING, required=True)
    fields.check_and_set(TASK_FIELD_OWNER, required=True)
    fields.check_and_set(TASK_FIELD_SOURCE, required=True)
    fields.check_and_set(TASK_FIELD_ID, required=True)
    fields.check_and_set(TASK_FIELD_TYPE, required=True)
    fields.check_and_set(TASK_FIELD_NEXT_TIME)
    return fields


class TimeBasedTask:

    def __init__(self, fields: TaskFields):
        self._fields = fields

        self._calculator = choose_calculator(self.date_string)()
        if self._calculator is None:
            raise ValueError("Time calculator must not be None")

    def __lt__(self, other: "TimeBasedTask"):
        if self.next_time is None:
            return False
        elif other.next_time is None:
            return True
        return self.next_time < other.next_time

    @property
    def date_string(self) -> str:
        return self._fields.get(TASK_FIELD_DATE_STRING)

    @property
    def next_time(self) -> Optional[datetime]:
        next_time = self._fields.get(TASK_FIELD_NEXT_TIME)
        if next_time is None:
            return next_time
        else:
            return datetime.strptime(next_time, DATE_CONVERTER)

    @property
    def source(self) -> str:
        return self._fields.get(TASK_FIELD_SOURCE)

    @property
    def author(self) -> int:
        return self._fields.get(TASK_FIELD_OWNER)

    @property
    def identifier(self) -> str:
        return self._fields.get(TASK_FIELD_ID)

    @property
    def fields(self) -> TaskFields:
        return self._fields

    def set_next_time(self, time: Optional[datetime] = None):
        if time is None:
            if self.next_time is None:
                time = datetime.now().replace(microsecond=0)
            else:
                time = self.next_time
        self._fields.set(
            TASK_FIELD_NEXT_TIME,
            self._calculator.calculate_next_date_with_context(self.date_string, time).strftime(DATE_CONVERTER)
        )

    def run(self) -> Optional[tuple[str, Any]]:
        pass

    def execute(self):
        return self.run()
