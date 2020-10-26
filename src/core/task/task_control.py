import importlib
import os
from core.task import task_base as tk
from datetime import datetime as dt, timedelta as td
from queue import PriorityQueue
from multiprocessing import Process
from threading import Thread
from core.containers import TaskContainer
from core.system.ipc import IPC
import time
from core.enums import Dates
from core.exceptions import UserHasNoTasksException, TaskIdDoesNotExistException, TaskCreationError


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)

    return decorator


class TaskExecutor(Thread):
    def __init__(self, tsk: tk.TimeBasedTask, ipc: IPC):
        Thread.__init__(self)
        self.task = tsk
        self.ipc = ipc

    def run(self):
        try:
            message = self.task.run()
        except Exception as e:
            message = "send", f"An exception occurred while executing your task: {e}"

        if message is not None:
            pkt = self.ipc.pack()
            self.ipc.send(dst="bot",
                          package=pkt,
                          author_id=self.task.author_id,
                          channel_id=self.task.channel_id,
                          cmd=message[0],
                          message=message[1])

        if self.task.delete:
            del self.task


class TaskManager(Process):

    def __init__(self, data, ipc: IPC):
        Process.__init__(self)
        # Queues
        self.task_queue = PriorityQueue()
        self.ipc = ipc

        self.core_tasks_path = "./core/tasks"
        self.core_import_tasks_path = "core.tasks"
        self.data = data

        self.tasks = {}  # author mapping
        self.task_dict = {}  # task classes

        self.next_date = None

        self.register_all_tasks()
        self.import_tasks(self.data.load("tasks"))

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
        for file in os.listdir(self.core_tasks_path):
            if file.endswith(".py") and not file.startswith("__"):
                self.register_task(self.core_import_tasks_path, file[:-3])

    def import_tasks(self, tasks: list):
        for t in tasks:
            self.add_task_from_dict(t)
        self.set_next_date()

    def export_tasks(self):
        tasks = []
        for v in self.tasks.values():
            for t in v:
                tasks.append(t.to_json())
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
        self.task_queue.put((tsk.next_time, tsk.creation_time, tsk))  # task is added to queue
        self.tasks[pkt.author_id].append(tsk)  # task is appended to author list

    def add_task_from_dict(self, tsk_dict: dict):
        if dt.now() > dt.strptime(tsk_dict["extra"]["next_time"], Dates.DATE_FORMAT.value) and \
                tsk_dict["extra"]["delete"]:
            return
        if tsk_dict["basic"]["author_id"] not in self.tasks.keys():
            self.tasks[tsk_dict["basic"]["author_id"]] = []
        tsk: tk.TimeBasedTask = self.task_dict[tsk_dict["extra"]["type"]](**tsk_dict["basic"])
        tsk.kwargs = tsk_dict["basic"]
        tsk.from_json(tsk_dict)
        if " " in tsk_dict["basic"]["date_string"]:
            next_time = tsk.get_next_date()
        else:
            next_time = dt.strptime(tsk_dict["extra"]["next_time"], Dates.DATE_FORMAT.value)
        self.tasks[tsk_dict["basic"]["author_id"]].append(tsk)
        self.task_queue.put((next_time, tsk.creation_time, tsk))

    def delete_task_from_mapping(self, tsk: tk.TimeBasedTask):
        author_id = tsk.author_id
        self.tasks[author_id].remove(tsk)

    def delete_task_from_queue(self, tsk: tk.TimeBasedTask):
        for t in self.task_queue.queue:
            if t[2] == tsk:
                self.task_queue.queue.remove(t)
                return
        raise RuntimeError("Task not in queue")

    def delete_task(self, tsk: tk.TimeBasedTask):
        self.delete_task_from_mapping(tsk)
        self.delete_task_from_queue(tsk)
        del tsk

    def get_task(self, task_id, author_id):
        if author_id not in self.tasks.keys():
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) == 0:
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) <= task_id:
            raise TaskIdDoesNotExistException("Task id does not exist")
        return self.tasks[author_id][task_id]

    def get_tasks(self, author_id):
        if author_id not in self.tasks.keys():
            raise UserHasNoTasksException("No active tasks")
        elif len(self.tasks[author_id]) == 0:
            raise UserHasNoTasksException("No active tasks")
        tasks = []
        for t in self.tasks[author_id]:
            tasks.append(t.to_json())
        return tasks

    def set_next_date(self):
        if not self.task_queue.empty():
            tsk = self.task_queue.get()
            self.next_date = tsk[0]
            self.task_queue.put(tsk)
        else:
            self.next_date = None

    def check_date(self):
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
                new_task_tuple = (tsk.get_next_date(), tsk.creation_time, tsk)
                self.task_queue.put(new_task_tuple)
            else:
                self.delete_task_from_mapping(tsk)
            self.set_next_date()
            executor = TaskExecutor(tsk, self.ipc)
            executor.start()

    def parse_commands(self, pkt):
        if pkt is not None:
            try:
                if pkt.cmd == "stop":
                    self.data.save(self.export_tasks(), "tasks")
                    return "stop"
                elif pkt.cmd == "task":
                    self.add_task(pkt)
                    self.set_next_date()
                elif pkt.cmd == "get_tasks":
                    tasks = self.get_tasks(pkt.author_id)
                    pkt.pipe.send(tasks)
                elif pkt.cmd == "del_task":
                    tsk = self.get_task(int(pkt.task_id) - 1, pkt.author_id)
                    self.delete_task(tsk)
                    pkt.pipe.send(None)
            except Exception as e:
                if pkt.pipe is not None:
                    pkt.pipe.send(e)
                else:
                    self.ipc.send(dst="bot", package=pkt,
                                  cmd="send",
                                  message=f"<p>An error occurred in the Task Manager: {e}")

        return None

    def run(self):
        while True:
            pkt = self.ipc.check_queue("task")
            stop = self.parse_commands(pkt)
            if stop == "stop":
                break
            self.tasks_loop()
            time.sleep(0.2)