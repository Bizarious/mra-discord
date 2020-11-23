from unittest import TestCase
from datetime import datetime as dt, timedelta as td
from core.task.task_control import TaskManager
from core.system import IPC
from core.database import Data
from core.containers import TransferPackage


class TaskManagerTests(TestCase):
    tm: TaskManager
    ipc: IPC
    data: Data
    t: TransferPackage

    def setUp(self) -> None:
        self.ipc = IPC()
        self.ipc.create_queues("bot", "task")
        self.data = Data()
        self.tm = TaskManager(data=self.data, ipc=self.ipc)
        self.tm.paths = {"../src/tasks": "tasks"}
        self.tm.register_all_tasks()
        self.t = TransferPackage()
        self.t.pack(author_id=0,
                    channel_id=0,
                    message="test",
                    message_args="",
                    date_string="1h",
                    label="test",
                    number=0
                    )

        self.t.label(dst="task",
                     cmd="task",
                     task="Reminder",
                     author_id=0,
                     channel_id=0
                     )

        self.tm.add_task(self.t)

    def tearDown(self) -> None:
        self.data.set_json(file="tasks", data=[])

    def test_add_task_right_next_date(self):
        self.tm.add_task(self.t)
        right_next_time = dt.now().replace(microsecond=0) + td(hours=1)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_add_second_later_task_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=0,
                channel_id=0,
                message="test",
                message_args="",
                date_string="2h",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=0,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        right_next_time = dt.now().replace(microsecond=0) + td(hours=1)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_add_second_earlier_task_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=0,
                channel_id=0,
                message="test",
                message_args="",
                date_string="30m",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=0,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        right_next_time = dt.now().replace(microsecond=0) + td(minutes=30)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_remove_only_task_right_date(self):
        task = self.tm.get_task(0, 0)
        self.tm.delete_task(task)

        self.assertEqual(None, self.tm.next_date)

    def test_remove_first_task_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=0,
                channel_id=0,
                message="test",
                message_args="",
                date_string="2h",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=0,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        task = self.tm.get_task(0, 0)
        self.tm.delete_task(task)
        right_next_time = dt.now().replace(microsecond=0) + td(hours=2)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_remove_second_task_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=0,
                channel_id=0,
                message="test",
                message_args="",
                date_string="2h",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=0,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        task = self.tm.get_task(1, 0)
        self.tm.delete_task(task)
        right_next_time = dt.now().replace(microsecond=0) + td(hours=1)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_remove_all_tasks_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=0,
                channel_id=0,
                message="test",
                message_args="",
                date_string="2h",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=0,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        self.tm.delete_all_tasks(0)

        self.assertEqual(self.tm.next_date, None, msg="Wrong next date")

    def test_add_second_task_different_user_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=1,
                channel_id=0,
                message="test",
                message_args="",
                date_string="30m",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=1,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        right_next_time = dt.now().replace(microsecond=0) + td(minutes=30)

        self.assertEqual(self.tm.next_date, right_next_time, msg="Wrong next date")

    def test_load_tasks_right_date(self):
        t2 = TransferPackage()
        t2.pack(author_id=1,
                channel_id=0,
                message="test",
                message_args="",
                date_string="30m",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=1,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        right_next_time = dt.now().replace(microsecond=0) + td(minutes=30)
        self.tm.next_date = None
        while not self.tm.task_queue.empty():
            self.tm.task_queue.get()
        self.tm.tasks = {}
        self.tm.import_tasks(self.data.get_json(file="tasks"))

        self.assertEqual(right_next_time, self.tm.next_date)

    def test_delete_all_tasks_multiple_users(self):
        t2 = TransferPackage()
        t2.pack(author_id=1,
                channel_id=0,
                message="test",
                message_args="",
                date_string="30m",
                label="test",
                number=0
                )

        t2.label(dst="task",
                 cmd="task",
                 task="Reminder",
                 author_id=1,
                 channel_id=0
                 )

        self.tm.add_task(t2)
        self.tm.delete_all_tasks(0)
        self.tm.delete_all_tasks(1)

        self.assertEqual(None, self.tm.next_date)
