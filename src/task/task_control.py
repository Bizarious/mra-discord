import importlib
import os
import task.task_base as tk
from datetime import datetime as dt, timedelta as td
from queue import PriorityQueue
from multiprocessing import Queue, Process
from containers import TaskContainer, TransferPackage
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
        self.task_queue = PriorityQueue()

        self.tasks_path = "../tasks"
        self.import_tasks_path = "tasks"

        self.tasks = {}
        self.task_dict = {}

        self.next_date = None

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
        if str(pkt.author_id) not in self.tasks.keys():
            self.tasks[str(pkt.author_id)] = []     # author id in task list
        tsk: tk.TimeBasedTask = self.task_dict[pkt.task](**pkt.kwargs)  # task creation
        self.tasks[str(pkt.author_id)].append(tsk)  # task is appended to author list
        self.task_queue.put((tsk.creation_time, tsk.get_next_date(), t))    # task is added to queue

    def set_next_date(self):
        tsk = self.task_queue.get()
        self.next_date = tsk[1]
        self.task_queue.put(tsk)

    def check_date(self):
        delta = td(seconds=5)
        now = dt.now().replace(microsecond=0)
        if (now >= self.next_date) and (now <= self.next_date + delta):
            print("NOW")
            self.next_date = dt.now().replace(year=2021)

    def run(self):
        while True:
            """""
            if not self.queue_in.empty():
                m = self.queue_in.get()
                print(m)
                if m == "Stop":
                    break
            """""
            self.check_date()
            time.sleep(0.2)


if __name__ == "__main__":
    t = TaskManager("a", "b", "c")
    t.register_all_tasks()
    tr = TransferPackage(author_id=1, task="EinTestTask", date_string="5s")
    t.add_task(tr)
    t.set_next_date()
    print(t.next_date)
    t.run()
