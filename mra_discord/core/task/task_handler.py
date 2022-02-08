import signal

from multiprocessing import Process
from random import randint
from typing import Type
from queue import Queue, Empty

from core.task.task_base import TaskPackage, TimeBasedTask, TaskFields
from core.task.scheduler import TimeTaskScheduler
from core.ext import load_extensions_from_paths, ExtensionHandler
from core.ext.modules import ExtensionHandlerIPCModule

TASK_HANDLER_IDENTIFIER = "task"


class TaskHandler(Process):

    def __init__(self, task_paths: [str], extension_paths: [str]):
        Process.__init__(self)

        self._paths = task_paths

        self._task_classes = {}

        # maps all tasks to their ids
        self._tasks = {}

        self._time_scheduler = TimeTaskScheduler()

        # used to stop the scheduling instant
        self._stop_queue = Queue()

        self._extension_handler = ExtensionHandler(self, TASK_HANDLER_IDENTIFIER, *extension_paths)
        self._extension_handler.add_module(ExtensionHandlerIPCModule(TASK_HANDLER_IDENTIFIER))
        self._extension_handler.load_extensions_from_paths()

        self.register_all_tasks()

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def register_all_tasks(self):
        task_packages: list[TaskPackage] = load_extensions_from_paths(*self._paths, tps="TaskPackage")

        for task_package in task_packages:

            if task_package.name in self._task_classes:
                raise KeyError(f'The task class "{task_package.name}" already exists')

            self._task_classes[task_package.name] = task_package.task_class

    def stop(self, *_):
        self._stop_queue.put("")

    def cleanup(self):
        self._time_scheduler.complete_cleanup()
        self._extension_handler.stop_modules()
        self._extension_handler.unload_all_extensions()

    def run(self) -> None:
        self._extension_handler.start_modules()

        while True:
            self._time_scheduler.schedule()

            try:
                self._stop_queue.get(timeout=0.5)
            except Empty:
                pass
            else:
                break

        self.cleanup()

    def _create_unique_task_id(self) -> str:
        length = 3

        while True:
            identifier = ""
            for i in range(length):
                identifier += str(randint(0, 9))
            if identifier not in self._tasks:
                break
        return identifier

    @staticmethod
    def build_task(task_class: Type[TimeBasedTask], task_arguments: dict) -> TimeBasedTask:
        fields = TaskFields(task_arguments)
        return task_class(fields)

    def add_task_to_queue(self, task: TimeBasedTask):
        self._time_scheduler.add_task(task)

    def add_task(self, task_name: str, task_arguments: dict):
        task_class = self._task_classes[task_name]
        task = self.build_task(task_class, task_arguments)
        task.set_next_time()
        self._tasks[self._create_unique_task_id()] = task
        self.add_task_to_queue(task)
        print(self._tasks)
