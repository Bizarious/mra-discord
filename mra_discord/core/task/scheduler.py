from queue import PriorityQueue
from datetime import datetime, timedelta
from threading import Lock

from core.task.task_base import TimeBasedTask


TASKS_TO_BE_DELETED = "delete"
TASKS_TO_BE_EXECUTED = "execute"


class TimeTaskScheduler:

    def __init__(self):
        self._lock = Lock()
        self._task_queue = PriorityQueue()
        self._next_time = None

    def set_next_time(self):
        self._lock.acquire()

        try:
            if not self._task_queue.empty():
                task: TimeBasedTask = self._task_queue.get()
                self._next_time = task.next_time
                self._task_queue.put(task)
            else:
                self._next_time = None

        finally:
            self._lock.release()

    def schedule(self) -> dict[str: list[TimeBasedTask]]:
        finished_tasks: list[TimeBasedTask] = []
        tasks_to_execute: list[TimeBasedTask] = []

        if self._next_time is not None and \
                self._next_time <= datetime.now() <= self._next_time + timedelta(seconds=5):

            self._lock.acquire()
            try:

                while True:
                    if self._task_queue.empty():
                        break
                    task: TimeBasedTask = self._task_queue.get()
                    if task.next_time > self._next_time:
                        break
                    tasks_to_execute.append(task)

                for task in tasks_to_execute:
                    task: TimeBasedTask
                    task.set_next_time()
                    if task.next_time is not None:
                        self._task_queue.put(task)
                    else:
                        finished_tasks.append(task)

            finally:
                self._lock.release()
                self.set_next_time()

        return {
            TASKS_TO_BE_DELETED: finished_tasks,
            TASKS_TO_BE_EXECUTED: tasks_to_execute
                }

    def add_task(self, task: TimeBasedTask):
        self._task_queue.put(task)
        self.set_next_time()
