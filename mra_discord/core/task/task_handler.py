from queue import PriorityQueue
from multiprocessing import Process
from datetime import datetime as dt
from .task_base import TaskPackage
from .errors import TaskAlreadyExists
from core.ipc import IPC
from core.ext import load_extensions_from_paths, ExtensionHandler
from core.ext.modules import ExtensionHandlerIPCModule

TASK_HANDLER_IPC_IDENTIFIER = "task"


class TaskHandler(Process):

    def __init__(self, ipc_handler: IPC, *paths: str):
        Process.__init__(self)
        ipc_handler.add_queue(TASK_HANDLER_IPC_IDENTIFIER)

        # the paths, where it should look for tasks
        self._paths = paths

        # maps all task classes to their names
        self._task_classes = {}

        self._task_scheduler = TaskScheduler()
        self._extension_handler = ExtensionHandler(self)
        self._extension_handler.add_module(ExtensionHandlerIPCModule(ipc_handler, TASK_HANDLER_IPC_IDENTIFIER))

    def register_all_tasks(self):
        task_packages: list[TaskPackage] = load_extensions_from_paths(*self._paths, tps="TaskPackage")

        for task_package in task_packages:

            if task_package.name in self._task_classes:
                raise TaskAlreadyExists(f'The task class "{task_package.name}" already exists')

            self._task_classes[task_package.name] = task_package.task_class

    def run(self) -> None:
        self._extension_handler.start_modules()


class TaskScheduler:

    def __init__(self):
        # the queue the scheduler will pull from
        self._task_queue = PriorityQueue()
        self._next_time = None

    def set_next_time(self, time: dt):
        pass
