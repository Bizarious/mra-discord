class TransferPackage:
    def __init__(self, *, author_id, channel_id=None, server_id=None, task=None, **kwargs):
        self.author_id = author_id
        self.channel_id = channel_id
        self.server_id = server_id
        self.task = task
        self.kwargs = kwargs
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class TaskContainer:

    task_creatable = True

    def __init__(self, task_class, name):
        self.task_class = task_class
        self.name = name
