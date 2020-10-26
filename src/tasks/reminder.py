from task.task_base import TimeBasedTask
from task.task_control import task


@task("Reminder")
class Reminder(TimeBasedTask):
    def __init__(self, *, author_id, channel_id, server_id=None, date_string, label, message):
        TimeBasedTask.__init__(self, author_id=author_id,
                               channel_id=channel_id,
                               server_id=server_id,
                               date_string=date_string,
                               label=label)
        self.message = message

    def run(self):
        return "send", self.message
