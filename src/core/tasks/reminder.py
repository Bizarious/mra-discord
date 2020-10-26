from core.task import TimeBasedTask
from core.task import task


@task("Reminder")
class Reminder(TimeBasedTask):
    def __init__(self, *, author_id, channel_id, server_id=None, date_string, number, label, message):
        TimeBasedTask.__init__(self, author_id=author_id,
                               channel_id=channel_id,
                               server_id=server_id,
                               date_string=date_string,
                               label=label,
                               number=number)
        self.message = message

    def run(self):
        return "send", self.message
