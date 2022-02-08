import logging

from queue import PriorityQueue
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Optional

from core.task.task_base import TimeBasedTask


class TimeTaskScheduler:

    def __init__(self):
        self._lock = Lock()
        self._task_queue = PriorityQueue()
        self._running_tasks = []
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

    def schedule(self) -> Optional[list[TimeBasedTask]]:
        finished_tasks: list[TimeBasedTask] = []

        if self._next_time is not None and \
                self._next_time <= datetime.now() <= self._next_time + timedelta(seconds=5):

            self._lock.acquire()
            try:

                tasks = []
                while True:
                    if self._task_queue.empty():
                        break
                    task: TimeBasedTask = self._task_queue.get()
                    if task.next_time > self._next_time:
                        break
                    tasks.append(task)

                for task in tasks:
                    task: TimeBasedTask
                    task.set_next_time()
                    if task.next_time is not None:
                        self._task_queue.put(task)
                    else:
                        finished_tasks.append(task)
                    thread = Thread(target=task.execute)
                    thread.start()
                    self._running_tasks.append(thread)

            except Exception as e:
                logging.error(e)

            finally:
                self._lock.release()
                self.set_next_time()

            return finished_tasks

        return None

    def clean_terminated_tasks(self):
        task_thread: Thread
        self._running_tasks = [task_thread for task_thread in self._running_tasks if task_thread.is_alive()]

    def complete_cleanup(self):
        task_thread: Thread
        for task_thread in self._running_tasks:
            task_thread.join()

    def add_task(self, task: TimeBasedTask):
        self._task_queue.put(task)
        self.set_next_time()
