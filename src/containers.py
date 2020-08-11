class TransferPackage:
    def __init__(self, *, author, channel, **kwargs):
        self.kwargs = kwargs
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class TaskContainer:

    task_creatable = True

    def __init__(self, task_class, name):
        self.task_class = task_class
        self.name = name
