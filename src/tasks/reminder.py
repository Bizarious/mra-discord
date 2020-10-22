from task.task_base import TimeBasedTask
from task.task_control import task


@task("Reminder")
class Reminder(TimeBasedTask):
    def __init__(self, *, author_id, channel_id, date_string, message):
        TimeBasedTask.__init__(self, author_id=author_id, channel_id=channel_id, date_string=date_string)
        self.message = message
        print(self.date_string)

    def run(self):
        return self.message
