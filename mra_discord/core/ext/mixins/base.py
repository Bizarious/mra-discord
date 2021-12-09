from typing import Any


class ExtensionHandlerMixin:
    _interface: Any
    _accessible_types: list
    _to_be_executed_on_extension_loading: list
