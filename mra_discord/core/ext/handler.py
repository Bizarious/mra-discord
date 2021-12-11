from importlib.util import spec_from_file_location, module_from_spec
from typing import Any
from .errors import (ExtensionClassNotFoundError,
                     ExtensionAlreadyLoadedError,
                     ExtensionNotLoadedError,
                     ExtensionCannotUnloadError
                     )
from .extension import ExtensionPackage

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


class ExtensionHandler:
    """
    The class used to manage extensions.
    """

    def __init__(self, interface, *paths: str):
        self._paths = paths
        self._interface = interface

        # collecting all types the handler can see
        self._accessible_types = []

        # list of functions that are executed on extension loading/unloading
        self._to_be_executed_on_extension_loading = []
        self._to_be_executed_on_extension_unloading = []

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

    def can_unload(self, name: str) -> bool:
        return self._extension_packages[name].can_unload

    def _add_extension_class(self, name: str, extension_package: ExtensionPackage) -> None:
        if name in self._extension_packages:
            raise RuntimeError(f'The extension "{name}" already exists')
        self._extension_packages[name] = extension_package

        # add all auto loading extensions to list
        if extension_package.auto_load:
            self._to_auto_load.append(extension_package)

    def _load_extension_from_file(self, name: str, path: str, tps: str) -> None:
        # loading module
        spec = spec_from_file_location(name, path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        extension_packages: [ExtensionPackage] = get_attributes(module,
                                                                tps
                                                                )[tps]
        for extension_package in extension_packages:
            self._add_extension_class(extension_package.name, extension_package)

    def load_extensions_from_paths(self) -> None:
        """
        Loads all extension classes that are found in the paths to the list.
        """
        for path in self._paths:
            for file in os.listdir(path):
                if not file.startswith("__") and file.endswith(".py"):
                    self._load_extension_from_file(file[:-3], path + f"/{file}", "ExtensionPackage")

        for extension in self._to_auto_load:
            self.load_extension(extension.name)

    def _execute_on_loading(self, attributes: dict, extension: Any) -> None:
        for func in self._to_be_executed_on_extension_loading:
            func(attributes, extension)

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

    def _execute_on_unloading(self, extension: Any):
        for func in self._to_be_executed_on_extension_unloading:
            func(extension)

    def _unload_extension(self, name: str):
        if name not in self._extensions:
            raise ExtensionNotLoadedError(f'Cannot unload "{name}": The extension class has not been loaded')

        extension = self._extensions.pop(name)

        for func in self._to_be_executed_on_extension_unloading:
            func(extension)

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
