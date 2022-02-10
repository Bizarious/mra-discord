import logging
import signal

from multiprocessing import Process
from queue import Queue, Empty
from random import randint
from threading import Thread
from typing import Type, Callable, Optional, Any

from core.bot import BOT_IDENTIFIER
from core.task.task_base import TaskPackage, TimeBasedTask, TaskFields, TASK_FIELD_ID
from core.task.scheduler import TimeTaskScheduler, TASKS_TO_BE_EXECUTED, TASKS_TO_BE_DELETED
from core.ext import load_extensions_from_paths, ExtensionHandler
from core.ext.modules import ExtensionHandlerIPCModule, ipc

TASK_HANDLER_IDENTIFIER = "task"

FIELD_IPC_TASK_RESULT = "content"

_logger = logging.getLogger(TASK_HANDLER_IDENTIFIER)


def handle_task_result_ipc(result: Optional[tuple[str, Any]], task: TimeBasedTask) -> None:
    connection = ipc.establish_connection(BOT_IDENTIFIER, TASK_HANDLER_IDENTIFIER)

    package = ipc.IPCPackage(command=result).pack(task.fields.raw_dict)

    connection.send_and_recv(package)
    connection.end_communication()


class TaskExecutorThread(Thread):

    def __init__(self,
                 task: TimeBasedTask,
                 result_handler: Callable[[Optional[tuple[str, Any]], TimeBasedTask], None]
                 ):

        super().__init__()
        self._task = task
        self._result_handler = result_handler

    def run(self) -> None:
        result = self._task.execute()
        if result is not None:
            self._result_handler(result, self._task)


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

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    @property
    def extension_handler(self):
        return self._extension_handler

    def register_all_tasks(self):
        task_packages: list[TaskPackage] = load_extensions_from_paths(*self._paths, tps="TaskPackage")

        for task_package in task_packages:

            if task_package.name in self._task_classes:
                raise KeyError(f'The task class "{task_package.name}" already exists')

            self._task_classes[task_package.name] = task_package.task_class

    def stop(self, *_):
        self._stop_queue.put("")

    def cleanup(self):
        self._extension_handler.stop_modules()
        self._extension_handler.unload_all_extensions()

    def run(self) -> None:
        self.register_all_tasks()
        self._extension_handler.load_extensions_from_paths()
        self._extension_handler.start_modules()
        _logger.info("Started successfully")

        while True:
            tasks_to_handle = self._time_scheduler.schedule()
            delete = tasks_to_handle[TASKS_TO_BE_DELETED]
            execute = tasks_to_handle[TASKS_TO_BE_EXECUTED]

            for e in execute:
                TaskExecutorThread(e, handle_task_result_ipc).start()
                _logger.debug(f"Executed {e.identifier}")
            for d in delete:
                self.remove_task_from_dict(d)

            # for ending the loop
            try:
                self._stop_queue.get(timeout=0.5)
            except Empty:
                pass
            else:
                break

        self.cleanup()
        _logger.info("Stopped successfully")

    def _create_unique_task_id(self) -> str:
        length = 3

        while True:
            identifier = ""
            for i in range(length):
                identifier += str(randint(0, 9))
            if identifier not in self._tasks:
                break
        return identifier

    def build_task(self, task_class: Type[TimeBasedTask], task_arguments: dict) -> TimeBasedTask:
        fields = TaskFields(task_arguments)
        fields.set(TASK_FIELD_ID, self._create_unique_task_id())
        return task_class(fields)

    def add_task_to_queue(self, task: TimeBasedTask):
        self._time_scheduler.add_task(task)

    def add_task(self, task_name: str, task_arguments: dict):
        task_class = self._task_classes[task_name]
        task = self.build_task(task_class, task_arguments)
        self._tasks[task.identifier] = task
        task.set_next_time()
        self.add_task_to_queue(task)
        _logger.debug(f"Added {task.identifier} - tasks: {self._tasks}")

    def remove_task_from_dict(self, task: TimeBasedTask):
        if task.identifier not in self._tasks:
            raise KeyError(f"The task with id '{task.identifier}' is not found")
        self._tasks.pop(task.identifier)
        _logger.debug(f"Deleted {task.identifier} - tasks: {self._tasks}")

    def get_task_by_id(self, identifier: str) -> TimeBasedTask:
        if identifier not in self._tasks:
            raise KeyError(f"The task with id {identifier} does not exist")
        return self._tasks[identifier]

    def get_all_tasks(self) -> dict[str: TimeBasedTask]:
        return {k: v for k, v in self._tasks.items()}
