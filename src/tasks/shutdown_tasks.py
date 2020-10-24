from task.task_base import TimeBasedTask
from task.task_control import task


@task("Shutdown")
class ShutdownTask(TimeBasedTask):
    def __init__(self, *, author_id, channel_id=None, server_id=None, date_string):
        TimeBasedTask.__init__(self,
                               author_id=author_id,
                               channel_id=channel_id,
                               server_id=server_id,
                               date_string=date_string)
        self.delete = True

    def run(self):
        return "shutdown", None
