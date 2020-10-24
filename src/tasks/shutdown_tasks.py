from task.task_base import TimeBasedTask
from task.task_control import task


@task("Shutdown")
class ShutdownTask(TimeBasedTask):
    def __init__(self, *, author_id, date_string):
        TimeBasedTask.__init__(self, author_id=author_id, date_string=date_string)
        self.delete = True

    def run(self):
        return "shutdown", None
