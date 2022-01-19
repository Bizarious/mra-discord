from queue import PriorityQueue
from multiprocessing import Process
from datetime import datetime as dt
from .task_base import TaskPackage
from .errors import TaskAlreadyExists
from core.ext import load_extensions_from_paths


class TaskHandler(Process):

    def __init__(self, *paths: str):
        Process.__init__(self)

        # the paths, where it should look for tasks
        self._paths = paths

        # maps all task classes to their names
        self._task_classes = {}

        # the scheduler
        self._task_scheduler = TaskScheduler()

    def register_all_tasks(self):
        task_packages: list[TaskPackage] = load_extensions_from_paths(*self._paths, tps="TaskPackage")

        for task_package in task_packages:

            if task_package.name in self._task_classes:
                raise TaskAlreadyExists(f'The task class "{task_package.name}" already exists')

            self._task_classes[task_package.name] = task_package.task_class

    def run(self) -> None:
        pass



class TaskScheduler:

    def __init__(self):
        # the queue the scheduler will pull from
        self._task_queue = PriorityQueue()
        self._next_time = None

    def set_next_time(self, time: dt):
        pass

