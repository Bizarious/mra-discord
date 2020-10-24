from task.task_base import TimeBasedTask
from task.task_control import task


@task("Reminder")
class Reminder(TimeBasedTask):
    def __init__(self, *, author_id, channel_id, server_id=None, date_string, message):
        TimeBasedTask.__init__(self, author_id=author_id,
                               channel_id=channel_id,
                               server_id=server_id,
                               date_string=date_string)
        self.message = message

    def run(self):
        return "send", self.message

    def to_json(self):
        d = TimeBasedTask.to_json(self)
        d["basic"]["message"] = self.message
        return d
