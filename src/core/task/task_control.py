import importlib
import os
from abc import abstractmethod
from typing import Union
from core.task import task_base as tk
from datetime import datetime as dt, timedelta as td
from queue import PriorityQueue
from multiprocessing import Process
from threading import Thread, Lock
from core.containers import TaskContainer
from core.system import IPC
import time
from core.enums import Dates
from core.task.task_exceptions import UserHasNoTasksException, TaskIdDoesNotExistException, TaskCreationError
from core.database import Data, ConfigManager
from core.system import IPCPackageHandler


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)

    return decorator


class IPCTaskHandler(IPCPackageHandler):
    """
    Abstract class for a node of the task-manager's ipc-handler chain
    """

    def __init__(self, task_manager, next_node):
        IPCPackageHandler.__init__(self, next_node)

        # pointer to the task manager for calling functions
        self.task_manager = task_manager

    @abstractmethod
    def handle(self, pkt):
        pass


class TaskLimiter:

    def __init__(self, data: Data, config: ConfigManager):
        self.data = data
        self.config = config

        self.config.set_default_config("taskLimit", "Tasks", "5")
        self.config.set_default_config("systemTaskLimit", "Tasks", "10")
        self.config.set_default_config("applyTaskLimitToOwner", "Tasks", "True")

        self.task_limit = int(self.config.get_config("taskLimit", "Tasks"))
        self.limit_owner = self.config.get_config("applyTaskLimitToOwner", "Tasks")
        self.limit_system = int(self.config.get_config("systemTaskLimit", "Tasks"))
        self.bot_owner = int(self.config.get_config("botOwner", "General"))

        self.limits = self.data.get_json(file="limits", path="tasks")

        # system commands get extra limit
        self.limits["0"] = self.limit_system

    def reached_limit(self, uid: int, number: int):
        if self.limit_owner == "False" and uid == self.bot_owner:
            return False
        elif str(uid) in self.limits.keys():

            # -1: no limit
            if self.limits[str(uid)] == -1:
                return False
            elif self.limits[str(uid)] <= number:
                return True
            return False
        elif self.task_limit == -1:
            return False
        elif number >= self.task_limit:
            return True
        return False

    def get_limit(self, uid: int):
        if str(uid) in self.limits.keys():
            return self.limits[str(uid)]
        return self.task_limit

    def add_limit(self, uid: int, value: int):
        self.limits[str(uid)] = value
        self.data.set_json(file="limits", path="tasks", data=self.limits)

    def remove_limit(self, uid: int):
        del self.limits[str(uid)]
        self.data.set_json(file="limits", path="tasks", data=self.limits)


class TaskExecutor(Thread):
    def __init__(self, tsk: tk.TimeBasedTask, manager):
        Thread.__init__(self)
        self.task = tsk
        self.manager = manager

    def run(self):
        try:
            message = self.task.execute()
        except Exception as e:
            message = "send", f"An exception occurred while executing your task: {e}"

        if message is not None:
            pkt = self.manager.ipc.pack()
            self.manager.ipc.send(dst="bot",
                                  package=pkt,
                                  author_id=self.task.author_id,
                                  channel_id=self.task.channel_id,
                                  cmd=message[0],
                                  message=message[1],
                                  message_args=message[2])

        self.manager.running_tasks_lock.acquire()
        self.manager.running_tasks.remove(self)
        self.manager.running_tasks_lock.release()


class TaskManager(Process):

    def __init__(self, data: Data, config: ConfigManager, ipc: IPC):
        Process.__init__(self)

        # holds all nodes of the chain
        self.nodes: [IPCTaskHandler] = []
        self.ipc_handler = None

        # Queues
        self.task_queue = PriorityQueue()
        self.ipc = ipc
        self.running_tasks = []
        self.running_tasks_lock = Lock()

        self.paths = {"./tasks": "tasks"}
        self.data: Data = data
        self.config = config
        self.task_limiter = TaskLimiter(self.data, self.config)

        self.tasks = {}  # author mapping
        self.task_dict = {}  # task classes

        self.next_date = None

        self.register_all_tasks()

    def load_tasks(self) -> list:
        return self.data.get_json(file="tasks", path="tasks")

    def register_chain(self):
        for n in self.nodes:
            self.ipc_handler = n(self, self.ipc_handler)

    def register_task(self, module_path: str, file: str):
        task_module = importlib.import_module(f'{module_path}.{file}')

        # search for objects
        for obj in dir(task_module):
            try:
                container: TaskContainer = getattr(task_module, obj)
                getattr(container, "task_creatable")
            except AttributeError:
                pass
            else:
                # object found
                task_class = container.task_class
                name = container.name
                self.task_dict[name] = task_class

    def register_all_tasks(self):
        for path in self.paths.keys():
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(".py") and not file.startswith("__"):
                        self.register_task(self.paths[path], file[:-3])

    def run(self) -> None:
        pass


if __name__ == "__main__":
    pass
