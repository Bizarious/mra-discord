from datetime import datetime
from typing import Optional, Type, Any

from core.task.time_calculator import choose_calculator
from core.ext.modules import ipc

TASK_FIELD_DATE_STRING = "date_string"
TASK_FIELD_NEXT_TIME = "next_time"
TASK_FIELD_SOURCE = "source"
TASK_FIELD_ID = "id"
TASK_FIELD_OWNER = ipc.CONTENT_FIELD_AUTHOR


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

    def get(self, key: str):
        return self._raw_dict.get(key)

    def set(self, key: str, value: Any):
        self._raw_dict[key] = value

    def check_and_set(self, key: str, default: Any = None, required: bool = False):
        if key not in self._raw_dict.keys():
            if required:
                raise KeyError(f"The field '{key}' is required")
            self._raw_dict[key] = default


class TimeBasedTask:

    def __init__(self, fields: TaskFields):
        fields.check_and_set(TASK_FIELD_DATE_STRING, required=True)
        fields.check_and_set(TASK_FIELD_OWNER, required=True)
        fields.check_and_set(TASK_FIELD_SOURCE, required=True)
        fields.check_and_set(TASK_FIELD_ID, required=True)
        fields.check_and_set(TASK_FIELD_NEXT_TIME)

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
        return self._fields.get(TASK_FIELD_NEXT_TIME)

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
            self._calculator.calculate_next_date_with_context(self.date_string, time)
        )

    def run(self) -> Optional[tuple[str, Any]]:
        pass

    def execute(self):
        return self.run()
