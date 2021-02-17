import importlib
import os
from abc import abstractmethod, ABC
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
from core.database import Data, ConfigManager
from core.system import IPCPackageHandler


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)

    return decorator


class IPCTaskHandler(IPCPackageHandler):
    """
    Abstract class for a node of the task-manager's ipc-handler chain.
    """

    def __init__(self, task_manager, next_node):
        IPCPackageHandler.__init__(self, next_node)

        # pointer to the task manager for calling functions
        self.task_manager: TaskManager = task_manager

    @abstractmethod
    def handle(self, pkt):
        pass


class TaskAdder(IPCTaskHandler):
    cmd = ["add_task", "delete_task"]

    def add_task(self, pkt):
        name = pkt.task
        tsk = self.task_manager.task_factory.produce(name, **pkt.kwargs)
        tsk.next_date = tsk.calc_next_date()
        if tsk is not None:
            self.task_manager.add_tasks(tsk, author_id=pkt.author_id)

    def delete_task(self, pkt):
        index = pkt.task_id
        author_id = pkt.author_id
        tsk = self.task_manager.get_task(author_id, index)
        self.task_manager.remove_tasks(tsk, author_id=author_id)

    def handle(self, pkt):
        if pkt.cmd == "add_task":
            self.add_task(pkt)
        elif pkt.cmd == "delete_task":
            self.delete_task(pkt)


class TaskGetter(IPCTaskHandler):
    cmd = ["get_tasks"]

    def handle(self, pkt):
        dicts = self.task_manager.export_tasks(pkt.author_id, Dates.DATE_FORMAT.value)
        return dicts


class TaskManagerStopper(IPCTaskHandler):
    cmd = ["stop"]

    def handle(self, pkt):
        return "stop"


class TaskFactory:
    """
    The factory class for creating tasks.
    """

    def __init__(self, tasks: dict):
        self.tasks = tasks

    def produce(self, name: str, extra_dict: dict = None, **kwargs) -> Union[tk.TimeBasedTask, None]:
        if name in self.tasks.keys():
            task_class = self.tasks[name]
            t: tk.TimeBasedTask = task_class(**kwargs)
            t.kwargs = kwargs
            t.name = name
            if extra_dict is not None:
                t.from_json(extra_dict)
            return t
        return None


class TimeBasedScheduler(ABC):
    """
    Abstract class for the scheduler-implementation.
    """

    def __init__(self):
        self.next_date = None
        self.task_queue = PriorityQueue()

    @abstractmethod
    def schedule(self):
        pass

    def add_task(self, tsk: tk.Task):
        self.task_queue.put(tsk)

    def remove_task(self, *tsk: tk.Task):
        for t in tsk:
            if t in self.task_queue.queue:
                self.task_queue.queue.remove(t)

    def calc_next_date(self):
        if not self.task_queue.empty():
            tsk: tk.TimeBasedTask = self.task_queue.get()
            self.next_date = tsk.next_date
            self.task_queue.put(tsk)
        else:
            self.next_date = None


class DefaultTimeBasedScheduler(TimeBasedScheduler):
    """
    The default implementation of the scheduler.
    """

    def schedule(self) -> Union[tk.Task, None]:
        now = dt.now()

        # now between 5 seconds from next date
        if self.next_date is not None:
            if self.next_date <= now <= self.next_date + td(seconds=5):
                tsk: tk.TimeBasedTask = self.task_queue.get()
                tsk.next_date = tsk.calc_next_date()
                self.task_queue.put(tsk)
                self.calc_next_date()
                return tsk
        return None


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
    def __init__(self, tsk: tk.Task, manager):
        Thread.__init__(self)
        self.task = tsk
        self.manager = manager

    def run(self):
        try:
            message = self.task.run()
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
    """
    Implementation of the task manager. Runs in a separate process. Manages task creation and scheduling.
    """

    def __init__(self, data: Data, config: ConfigManager, ipc: IPC):
        Process.__init__(self)

        # holds all classes which shall be instantiated and appended to the chain
        self.nodes: [IPCTaskHandler] = [TaskManagerStopper, TaskAdder, TaskGetter]
        self.ipc_handler: Union[None, IPCTaskHandler] = None
        self.register_chain()

        # Queues
        self.ipc = ipc
        self.running_tasks = []
        self.running_tasks_lock = Lock()

        self.paths = {"./tasks": "tasks"}
        self.data: Data = data
        self.config = config
        self.task_limiter = TaskLimiter(self.data, self.config)

        self.tasks = {}  # author mapping
        self.task_dict = {}  # task classes

        self.register_all_tasks()
        self.task_factory = TaskFactory(self.task_dict)
        self.ts = DefaultTimeBasedScheduler()  # the scheduler

    def get_task_class(self, name: str) -> Union[tk.Task, None]:
        """
        Returns the desired task class by name.
        """
        if name in self.task_dict.keys():
            return self.task_dict[name]
        return None

    def load_tasks(self) -> list:
        return self.data.get_json(file="tasks", path="tasks")

    def save_tasks(self):
        tasks = []
        for author in self.tasks.keys():
            for t in self.export_tasks(author, Dates.DATE_FORMAT_DETAIL.value):
                tasks.append(t)
        self.data.set_json(file="tasks", path="tasks", data=tasks)

    def register_chain(self):
        """
        Builds the chain of responsibility.
        """
        for n in self.nodes:
            self.ipc_handler = n(self, self.ipc_handler)

    def register_task(self, module_path: str, file: str):
        """
        Registers a task decorated with "task".
        """
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
        """
        Registers all tasks in the paths.
        """
        for path in self.paths.keys():
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(".py") and not file.startswith("__"):
                        self.register_task(self.paths[path], file[:-3])

    def add_tasks(self, *tsk: tk.Task, author_id: int):
        if author_id not in self.tasks.keys():
            self.tasks[author_id] = []
        for t in tsk:
            self.tasks[author_id].append(t)
            self.ts.add_task(t)
        self.ts.calc_next_date()
        self.save_tasks()

    def remove_tasks(self, *tsk: tk.Task, author_id: int):
        if author_id in self.tasks.keys():
            for t in tsk:
                if t in self.tasks[author_id]:
                    self.tasks[author_id].remove(t)
                    self.ts.remove_task(t)
        self.ts.calc_next_date()
        self.save_tasks()

    def get_task(self, author_id: int, index: int) -> Union[tk.Task, None]:
        if author_id in self.tasks.keys():
            if len(self.tasks[author_id]) >= index:
                return self.tasks[author_id][index - 1]
        return None

    def import_tasks(self):
        """
        Imports tasks from a list. Used at startup to load all old tasks.
        """
        task_list = self.load_tasks()
        tasks = {}
        for t in task_list:
            author = t["arguments"]["author_id"]
            name = t["extra"]["type"]
            args = t["arguments"]
            extra = t["extra"]
            tsk = self.task_factory.produce(name, extra, **args)
            if author not in tasks.keys():
                tasks[author] = []
            tasks[author].append(tsk)

        for a in tasks.keys():
            self.add_tasks(*tasks[a], author_id=a)

    def export_tasks(self, author_id: int, format_string: str) -> list:
        """
        Exports properties of all tasks of a user as dict.
        """
        dicts = []
        t: tk.Task
        if author_id in self.tasks.keys():
            for t in self.tasks[author_id]:
                dicts.append(t.to_json(format_string))
        return dicts

    def execute_task(self, tsk: tk.Task):
        te = TaskExecutor(tsk, self)
        self.running_tasks.append(te)
        te.start()

    def run(self) -> None:
        self.import_tasks()
        while True:
            pkt = self.ipc.check_queue("task")
            if pkt is not None:
                result = self.ipc_handler.parse_pkt(pkt)
                if result == "stop":
                    break
            tsk = self.ts.schedule()
            if tsk is not None:
                self.execute_task(tsk)
            time.sleep(0.2)


if __name__ == "__main__":
    pass
