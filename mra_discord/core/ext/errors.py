class ExtensionError(Exception):
    pass


class ExtensionClassNotFoundError(ExtensionError):
    pass


class ExtensionAlreadyLoadedError(ExtensionError):
    pass


class ExtensionNotLoadedError(ExtensionError):
    pass


class ExtensionCannotUnloadError(ExtensionError):
    pass
