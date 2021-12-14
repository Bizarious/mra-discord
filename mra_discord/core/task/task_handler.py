from queue import PriorityQueue
from .task_base import TaskPackage
from .errors import TaskAlreadyExists
from core.ext import load_extensions_from_paths


class TaskHandler:

    def __init__(self, *paths: str):
        # the paths, where it should look for tasks
        self._paths = paths

        # maps all task classes to their names
        self._task_classes = {}

        # the scheduler
        self._task_scheduler = TaskScheduler(self)

        # the queue the scheduler will pull from
        self._task_queue = PriorityQueue()

    def register_all_tasks(self):
        task_packages: list[TaskPackage] = load_extensions_from_paths(*self._paths, tps="TaskPackage")

        for task_package in task_packages:

            if task_package.name in self._task_classes:
                raise TaskAlreadyExists(f'The task class "{task_package.name}" already exists')

            self._task_classes[task_package.name] = task_package.task_class


class TaskScheduler:

    def __init__(self, task_handler: TaskHandler):
        # the reference is needed so that the scheduler can
        # pull, delete and re-add tasks from adn to the queue
        self._task_handler = task_handler
