import importlib
import os
from multiprocessing import Queue, Process
from containers import TaskContainer
import time


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)
    return decorator


class TaskManager(Process):

    def __init__(self, q_in, q_out, tasks):
        Process.__init__(self)
        # Queues
        self.queue_in: Queue = q_in
        self.queue_out: Queue = q_out

        self.tasks_path = "./tasks"
        self.import_tasks_path = "tasks"
        self.tasks = {}
        self.task_dict = {}

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

    def add_task(self, pkt):
        if str(pkt.author) not in self.tasks.keys():
            self.tasks[str(pkt.author)] = []
        self.tasks[str(pkt.author)].append(self.task_dict[pkt.task](**pkt.kwargs))

    def run(self):
        while True:
            if not self.queue_in.empty():
                m = self.queue_in.get()
                print(m)
                if m == "Stop":
                    break
            time.sleep(0.2)

