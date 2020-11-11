import importlib
import os
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
from .task_exceptions import UserHasNoTasksException, TaskIdDoesNotExistException, TaskCreationError
from core.database import Data


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)

    return decorator


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

    def __init__(self, data, ipc: IPC):
        Process.__init__(self)
        # Queues
        self.task_queue = PriorityQueue()
        self.ipc = ipc
        self.running_tasks = []
        self.running_tasks_lock = Lock()

        self.paths = {"./tasks": "tasks"}
        self.data: Data = data

        self.tasks = {}  # author mapping
        self.task_dict = {}  # task classes

        self.next_date = None

        self.register_all_tasks()

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

    def import_tasks(self, tasks: list):
        for t in tasks:
            self.add_task_from_dict(t)
        self.set_next_date()

    def export_tasks(self):
        tasks = []
        for v in self.tasks.values():
            t: tk.TimeBasedTask
            for t in v:
                tasks.append(t.to_json(Dates.DATE_FORMAT_DETAIL.value))
        return tasks

    def add_task(self, pkt):
        if pkt.author_id not in self.tasks.keys():
            self.tasks[pkt.author_id] = []  # author id in task list
        try:
            tsk: tk.TimeBasedTask = self.task_dict[pkt.task](**pkt.kwargs)  # task creation
        except Exception as e:
            raise TaskCreationError(f"Task could not be created: {e}")
        tsk.name = pkt.task
        tsk.kwargs = pkt.kwargs
        tsk.calc_counter()
        self.task_queue.put((tsk.next_time, tsk.creation_time, tsk))  # task is added to queue
        self.tasks[pkt.author_id].append(tsk)  # task is appended to author list
        self.data.set_json(file="tasks", data=self.export_tasks())

    def add_task_from_dict(self, tsk_dict: dict):
        # return, when task shall be deleted and next time is in the past
        if dt.now() > dt.strptime(tsk_dict["extra"]["next_time"], Dates.DATE_FORMAT.value) and \
                tsk_dict["extra"]["delete"]:
            return

        # author list is created
        if tsk_dict["basic"]["author_id"] not in self.tasks.keys():
            self.tasks[tsk_dict["basic"]["author_id"]] = []

        # task is created
        tsk: tk.TimeBasedTask = self.task_dict[tsk_dict["extra"]["type"]](**tsk_dict["basic"])
        tsk.kwargs = tsk_dict["basic"]
        tsk.from_json(tsk_dict)  # task gets dictionary with extra arguments

        # next time is calculated
        if dt.now() >= tsk.next_time:
            next_time = tsk.get_next_date(dt.now())
        else:
            next_time = tsk.next_time
        self.tasks[tsk_dict["basic"]["author_id"]].append(tsk)
        self.task_queue.put((next_time, tsk.creation_time, tsk))

    def delete_task_from_mapping(self, tsk: tk.Task):
        author_id = tsk.author_id
        self.tasks[author_id].remove(tsk)
        self.data.set_json(file="tasks", data=self.export_tasks())

    def delete_task_from_queue(self, tsk: tk.Task):
        for t in self.task_queue.queue:
            if t[2] == tsk:
                self.task_queue.queue.remove(t)
                return
        raise RuntimeError("Task not in queue")

    def delete_task(self, tsk: tk.Task):
        self.delete_task_from_mapping(tsk)
        self.delete_task_from_queue(tsk)
        del tsk
        self.set_next_date()

    def delete_all_tasks(self, uid: int):
        for t in self.tasks[uid]:
            self.delete_task_from_queue(t)
        self.tasks[uid] = []
        self.data.set_json(file="tasks", data=self.export_tasks())
        self.set_next_date()

    def get_task(self, task_id: int, author_id: int) -> tk.Task:
        if author_id not in self.tasks.keys():
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) == 0:
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) <= task_id:
            raise TaskIdDoesNotExistException("Task id does not exist")
        return self.tasks[author_id][task_id]

    def get_tasks(self, author_id: int) -> list:
        if author_id not in self.tasks.keys():
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) == 0:
            raise UserHasNoTasksException("No active tasks")
        tasks = []
        for t in self.tasks[author_id]:
            tasks.append(t.to_json(Dates.DATE_FORMAT.value))
        return tasks

    def set_next_date(self):
        if not self.task_queue.empty():
            tsk = self.task_queue.get()
            self.next_date = tsk[0]
            self.task_queue.put(tsk)
        else:
            self.next_date = None

    def check_date(self) -> bool:
        if self.next_date is not None:
            delta = td(seconds=5)
            now = dt.now().replace(microsecond=0)
            if (now >= self.next_date) and (now <= self.next_date + delta):
                return True
            return False
        return False

    def tasks_loop(self):
        if self.check_date():
            tsk_tuple: tuple = self.task_queue.get()
            tsk: tk.TimeBasedTask = tsk_tuple[2]
            if not tsk.delete:
                tsk.calc_counter()
                new_task_tuple = (tsk.get_next_date(), tsk.creation_time, tsk)
                self.task_queue.put(new_task_tuple)
            else:
                self.delete_task_from_mapping(tsk)
            self.set_next_date()
            executor = TaskExecutor(tsk, self)
            self.running_tasks.append(executor)
            executor.start()

    def parse_commands(self, pkt) -> Union[str, None]:
        if pkt is not None:
            try:
                if pkt.cmd == "stop":
                    return "stop"
                elif pkt.cmd == "wait":
                    return "wait"
                elif pkt.cmd == "task":
                    self.add_task(pkt)
                    self.set_next_date()
                elif pkt.cmd == "get_tasks":
                    tasks = self.get_tasks(pkt.author_id)
                    pkt.pipe.send(tasks)
                elif pkt.cmd == "del_task":
                    if pkt.task_id == "all":
                        self.delete_all_tasks(pkt.author_id)
                    else:
                        tsk = self.get_task(int(pkt.task_id) - 1, pkt.author_id)
                        self.delete_task(tsk)
                    pkt.pipe.send(None)
            except Exception as e:
                if pkt.pipe is not None:
                    pkt.pipe.send(e)
                else:
                    self.ipc.send(dst="bot", package=pkt,
                                  cmd="send",
                                  message=f"An error occurred in the Task Manager: {e}",
                                  message_args="p")

        return None

    def stop(self):
        t: Thread
        for t in self.running_tasks:
            t.join()
        self.data.set_json(file="tasks", data=self.export_tasks())  # tasks are saved

    def run(self):
        try:
            pkt = self.ipc.check_queue_block("task")
            if pkt.cmd == "stop":
                self.stop()
                return
            self.import_tasks(self.data.get_json(file="tasks"))
        except KeyboardInterrupt:
            self.stop()

        try:
            while True:
                pkt = self.ipc.check_queue("task")
                stop = self.parse_commands(pkt)
                if stop == "stop":
                    self.stop()
                    break
                elif stop == "wait":
                    self.data.set_json(file="tasks", data=self.export_tasks())
                    while not self.task_queue.empty():
                        self.task_queue.get()
                    self.tasks = {}
                    self.ipc.check_queue_block("task")
                    self.import_tasks(self.data.get_json(file="tasks"))
                self.tasks_loop()
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.stop()
