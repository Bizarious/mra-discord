from unittest import TestCase
from datetime import datetime as dt, timedelta as td
from tasks.reminder import Reminder
from core.task.task_exceptions import TaskCreationError
from croniter import croniter as cr


class TaskTests(TestCase):
    Rem = Reminder.task_class

    def test_right_date_hours(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="50h",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        right_date = dt.now().replace(microsecond=0) + td(hours=50)

        self.assertEqual(right_date, task.next_time)

    def test_right_date_minutes(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="31m",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        right_date = dt.now().replace(microsecond=0) + td(minutes=31)

        self.assertEqual(right_date, task.next_time)

    def test_right_date_seconds(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="7s",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        right_date = dt.now().replace(microsecond=0) + td(seconds=7)

        self.assertEqual(right_date, task.next_time)

    def test_right_date_complex(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="2h45m17s",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        right_date = dt.now().replace(microsecond=0) + td(hours=2, minutes=45, seconds=17)

        self.assertEqual(right_date, task.next_time)

    def test_right_date_cron_simple(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="* * * * *",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        dates = cr("* * * * *", dt.now())
        right_date = dates.get_next(dt)
        self.assertEqual(right_date, task.next_time)

    def test_right_date_cron_complex(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="20,35 5 25 1 *",
                                  number=0,
                                  label="test",
                                  message="test",
                                  message_args="")

        dates = cr("20,35 5 25 1 *", dt.now())
        right_date = dates.get_next(dt)
        self.assertEqual(right_date, task.next_time)

    def test_error_on_zero(self):
        try:
            self.Rem(author_id=0,
                     channel_id=0,
                     date_string="0s",
                     number=0,
                     label="test",
                     message="test",
                     message_args="")
        except TaskCreationError:
            self.assertTrue(True)
        else:
            self.assertFalse(True, msg="0 must throw and error")

    def test_execution_amount(self):
        task: Reminder = self.Rem(author_id=0,
                                  channel_id=0,
                                  date_string="5h",
                                  number=5,
                                  label="test",
                                  message="test",
                                  message_args="")

        for _ in range(4):
            task.calc_counter()
        self.assertFalse(task.delete)

        task.calc_counter()
        self.assertTrue(task.delete)
