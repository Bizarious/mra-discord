from task.task_base import TimeBasedTask
from task.task_control import task


@task("EinTestTask")
class TestTask(TimeBasedTask):
    def __init__(self, *, date_string):
        TimeBasedTask.__init__(self, author_id=1, date_string=date_string)
        self.counter = 0

    def run(self):
        print(self.counter)
        self.counter += 1
        if self.counter == 3:
            self.delete = True
