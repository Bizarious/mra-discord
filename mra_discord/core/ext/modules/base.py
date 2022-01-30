from core.ext import Extension


class ExtensionHandlerModule:

    def __init__(self):
        # maps all handlers to their extensions
        self._handlers = {}

    def _on_load(self, extension: Extension):
        pass

    def on_load(self, attributes: dict, extension: Extension):
        self._handlers[extension.name] = []
        for accessible_type in self.get_accessible_types():
            handlers: list[object] = attributes[accessible_type]

            for handler in handlers:
                self._handlers[extension.name].append(handler)

        self._on_load(extension)

    def _on_unload(self, extension: Extension):
        pass

    def on_unload(self, extension: Extension):
        self._on_unload(extension)
        self._handlers.pop(extension.name)

    def get_accessible_types(self) -> list[str]:
        return list()

    def start(self):
        pass

    def stop(self):
        pass
