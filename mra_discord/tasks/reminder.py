from typing import Optional, Any

from core.task import TimeBasedTask, task, TaskFields, TASK_FIELD_CHANNEL
from core.extensions.system import COMMAND_IPC_SEND, CONTENT_FIELD_MESSAGE


TASK_NAME = "Reminder"


def _reminder_fields_checker(fields: TaskFields) -> TaskFields:
    fields.check_and_set(CONTENT_FIELD_MESSAGE, required=True)
    fields.check_and_set(TASK_FIELD_CHANNEL)
    return fields


@task(TASK_NAME, _reminder_fields_checker)
class Reminder(TimeBasedTask):

    def run(self) -> Optional[tuple[str, Any]]:
        return COMMAND_IPC_SEND
