class IPCError(Exception):
    pass


class IPCQueueAlreadyExistsError(IPCError):
    pass


class IPCQueueDoesNotExistError(IPCError):
    pass
