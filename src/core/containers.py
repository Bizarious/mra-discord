class TransferPackage:
    def __init__(self):
        self.kwargs = None

    def pack(self, **kwargs):
        self.kwargs = kwargs

    def label(self, **kwargs):
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])


class TaskContainer:

    task_creatable = True

    def __init__(self, task_class, name: str):
        self.task_class = task_class
        self.name = name
