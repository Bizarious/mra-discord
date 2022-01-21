from importlib.util import spec_from_file_location, module_from_spec
from typing import Any, TYPE_CHECKING
from .errors import (ExtensionClassNotFoundError,
                     ExtensionAlreadyLoadedError,
                     ExtensionNotLoadedError,
                     ExtensionCannotUnloadError
                     )
from .extension import ExtensionPackage

if TYPE_CHECKING:
    from .modules.base import ExtensionHandlerModule

import os


def get_attributes(obj: object, *types: str) -> dict:
    """
    Searches through an object and returns a dictionary that contains the given types
    mapped to all attributes of that object, that are instances of that type.
    """

    # preparing the dictionary
    attribute_mapping = {}
    for t in types:
        attribute_mapping[t] = []

    # searching through the object
    for attribute_name in dir(obj):
        attribute = getattr(obj, attribute_name)
        for t in types:
            if attribute.__class__.__name__ == t:
                attribute_mapping[t].append(attribute)

    return attribute_mapping


def load_extensions_from_file(name: str, path: str, tps: str) -> list:
    # loading module
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    extension_packages: list = get_attributes(module, tps)[tps]

    return extension_packages


def load_extensions_from_paths(*paths: str, tps: str) -> list:
    """
    Loads all extension classes that are found in the paths to the list.
    """
    extension_packages = []
    for path in paths:
        for file in os.listdir(path):
            if not file.startswith("__") and file.endswith(".py"):
                extension_packages.extend(load_extensions_from_file(file[:-3], path + f"/{file}", tps))

    return extension_packages


class ExtensionHandler:
    """
    The class used to manage extensions.
    """

    def __init__(self, interface, *paths: str):
        self._paths = paths
        self._interface = interface

        # collects all modules
        self._modules = []

        # holds all types as strings that can be recognized
        self._accessible_types = []

        # maps all extension packages to their names
        self._extension_packages = {}
        self._to_auto_load = []

        # maps all loaded extension objects to their names
        self._extensions = {}

    @property
    def loaded_extensions(self) -> dict:
        return self._extensions

    @property
    def extension_packages(self) -> dict:
        return self._extension_packages

    def add_module(self, module: "ExtensionHandlerModule"):
        self._modules.append(module)
        self._accessible_types += module.get_accessible_types()

    def can_unload(self, name: str) -> bool:
        return self._extension_packages[name].can_unload

    def _add_extension_class(self, name: str, extension_package: ExtensionPackage) -> None:
        if name in self._extension_packages:
            raise RuntimeError(f'The extension "{name}" already exists')
        self._extension_packages[name] = extension_package

        # add all auto-loading extensions to list
        if extension_package.auto_load:
            self._to_auto_load.append(extension_package.name)

    def load_extensions_from_paths(self) -> None:
        extension_packages: [ExtensionPackage] = load_extensions_from_paths(*self._paths, tps="ExtensionPackage")
        for extension_package in extension_packages:
            self._add_extension_class(extension_package.name, extension_package)

        for name in self._to_auto_load:
            self.load_extension(name)

    def _execute_on_loading(self, attributes: dict, extension: Any) -> None:
        for module in self._modules:
            module.on_load(attributes, extension)

    def _execute_on_unloading(self, extension: Any):
        for module in self._modules:
            module.on_unload(extension)

    def load_extension(self, name: str, *args, **kwargs) -> None:
        """
        Loads an extension from the dict.
        """
        if name not in self._extension_packages:
            raise ExtensionClassNotFoundError(f'Cannot load "{name}": The extension class does not exist')
        if name in self._extensions:
            raise ExtensionAlreadyLoadedError(f'Cannot load "{name}": The extension has already been loaded')

        extension_package: ExtensionPackage = self._extension_packages[name]
        extension = extension_package.cls(self._interface, *args, **kwargs)
        attributes = get_attributes(extension, *self._accessible_types)
        self._execute_on_loading(attributes, extension)
        self._extensions[name] = extension

    def _unload_extension(self, name: str):
        if name not in self._extensions:
            raise ExtensionNotLoadedError(f'Cannot unload "{name}": The extension class has not been loaded')

        extension = self._extensions.pop(name)

        self._execute_on_unloading(extension)

    def unload_extension(self, name: str):
        if name not in self._extensions:
            raise ExtensionNotLoadedError(f'Cannot unload "{name}": The extension class has not been loaded')

        extension_package: ExtensionPackage = self._extension_packages[name]

        if not extension_package.can_unload:
            raise ExtensionCannotUnloadError(f'Cannot unload "{name}": The extension cannot be unloaded')

        self._unload_extension(name)

    def unload_all_extensions(self):
        extension_names = list(self._extensions.keys())[:]
        for extension_name in extension_names:
            self._unload_extension(extension_name)

    def start_modules(self):
        for module in self._modules:
            module.start()
