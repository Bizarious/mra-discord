class IPCError(Exception):
    pass


class IPCQueueAlreadyExists(IPCError):
    pass


class IPCQueueDoesNotExist(IPCError):
    pass
