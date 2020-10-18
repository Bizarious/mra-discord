from task.task_base import TimeBasedTask
from task.task_control import task


@task("EinTestTask")
class TestTask(TimeBasedTask):
    def __init__(self, *, date_string):
        TimeBasedTask.__init__(self, author_id=1, date_string=date_string)
