import importlib
import os
from multiprocessing import Queue
from queue import PriorityQueue
from datetime import datetime as dt
from itertools import count
from ..containers import TransferPackage, TaskContainer
import time


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)
    return decorator


class TaskManager:

    def __init__(self, q_in, q_out, tasks):
        # Queues
        self.queue_in: Queue = q_in
        self.queue_out: Queue = q_out

        self.tasks_path = "./tasks"
        self.import_tasks_path = "tasks"
        self.tasks = PriorityQueue()
        self.task_dict = tasks

    def register_task(self, module_path, file):
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
        for file in os.listdir(self.tasks_path):
            if file.endswith(".py") and not file.startswith("__"):
                self.register_task(self.import_tasks_path, file[:-3])

    def add_task(self, *, name, **kwargs):
        # TODO: Task adding
        self.tasks.put(self.task_dict[name](**kwargs))
