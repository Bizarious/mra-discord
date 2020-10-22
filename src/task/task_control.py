import importlib
import os
import task.task_base as tk
from datetime import datetime as dt, timedelta as td
from queue import PriorityQueue
from multiprocessing import Queue, Process
from threading import Thread, Lock
from containers import TaskContainer, TransferPackage
import time


def task(name):
    def decorator(task_class):
        return TaskContainer(task_class, name)
    return decorator


class TaskExecutor(Thread):
    def __init__(self, tsk: tk.TimeBasedTask, q_out: Queue):
        Thread.__init__(self)
        self.task = tsk
        self.q_out = q_out
        self.lock = Lock

    def run(self):
        message = self.task.run()
        if message is not None:
            self.q_out.put(message)
        if self.task.delete:
            del self.task


class TaskManager(Process):

    def __init__(self, q_in, q_out, tasks: dict):
        Process.__init__(self)
        # Queues
        self.queue_in: Queue = q_in
        self.queue_out: Queue = q_out
        self.task_queue = PriorityQueue()
        self.lock = Lock()

        self.tasks_path = "../tasks"
        self.import_tasks_path = "tasks"

        self.tasks = {}     # author mapping
        self.task_dict = {}     # task classes

        self.next_date = None

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
        for file in os.listdir(self.tasks_path):
            if file.endswith(".py") and not file.startswith("__"):
                self.register_task(self.import_tasks_path, file[:-3])

    def add_task(self, pkt: TransferPackage):
        if str(pkt.author_id) not in self.tasks.keys():
            self.tasks[pkt.author_id] = []     # author id in task list
        tsk: tk.TimeBasedTask = self.task_dict[pkt.task](**pkt.kwargs)  # task creation
        self.tasks[pkt.author_id].append(tsk)  # task is appended to author list
        self.task_queue.put((tsk.creation_time, tsk.get_next_date(), tsk))    # task is added to queue

    def delete_task_from_mapping(self, tsk: tk.TimeBasedTask):
        author_id = tsk.author_id
        self.tasks[author_id].remove(tsk)

    def delete_task_from_queue(self, tsk: tk.TimeBasedTask):
        self.task_queue.queue.remove(tsk)

    def set_next_date(self):
        if not self.task_queue.empty():
            tsk = self.task_queue.get()
            self.next_date = tsk[1]
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
                new_task_tuple = (tsk.creation_time, tsk.get_next_date(), tsk)
                self.task_queue.put(new_task_tuple)
            else:
                self.delete_task_from_mapping(tsk)
            self.set_next_date()
            executor = TaskExecutor(tsk, self.queue_out)
            executor.start()

    def run(self):
        while True:
            """""
            if not self.queue_in.empty():
                m = self.queue_in.get()
                print(m)
                if m == "Stop":
                    break
            """""
            self.tasks_loop()
            time.sleep(0.2)


if __name__ == "__main__":
    t = TaskManager("a", "b", {})
    t.register_all_tasks()
    tr = TransferPackage(author_id=1, task="EinTestTask", date_string="1s")
    t.add_task(tr)
    t.set_next_date()
    t.run()
