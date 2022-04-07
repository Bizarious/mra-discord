from core.task import TimeBasedTask
from core.task import task


# @task("Shutdown")
# class ShutdownTask(TimeBasedTask):
#     def __init__(self, *, author_id, channel_id=None, server_id=None, date_string, mode):
#         TimeBasedTask.__init__(self,
#                                author_id=author_id,
#                                channel_id=channel_id,
#                                server_id=server_id,
#                                date_string=date_string,
#                                label=mode)
#         self.mode = mode
#
#     def run(self):
#         return self.mode, None, None
