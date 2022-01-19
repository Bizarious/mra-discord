from typing import Any


class ExtensionHandlerModule:

    def on_load(self, attributes: dict, extension: Any):
        pass

    def on_unload(self, extension: Any):
        pass

    def get_accessible_types(self) -> list[str]:
        pass
