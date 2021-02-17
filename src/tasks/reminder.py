from core.task import TimeBasedTask
from core.task import task


@task("Reminder")
class Reminder(TimeBasedTask):
    def __init__(self, *, author_id, channel_id, server_id=None, date_string, label, message, message_args):
        TimeBasedTask.__init__(self, author_id=author_id,
                               channel_id=channel_id,
                               server_id=server_id,
                               date_string=date_string,
                               label=label,
                               min_interval=60
                               )

        self.message = message
        self.message_args = message_args

    def run(self):
        return "send", self.message, self.message_args
