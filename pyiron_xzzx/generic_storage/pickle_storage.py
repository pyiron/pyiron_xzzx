from __future__ import annotations

import pickle
from typing import Any

from pyiron_xzzx.generic_storage.interface import GenericStorage, StorageGroup


class PickleStorage(GenericStorage):
    def __init__(self, filename: str, mode="rb") -> None:
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.data: dict = {}

    def __enter__(self) -> PickleGroup:
        with open(self.filename, self.mode) as file:
            if file.readable():
                self.data = pickle.load(file)

        return PickleGroup(self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        with open(self.filename, self.mode) as file:
            if file.writable():
                pickle.dump(self.data, file, pickle.HIGHEST_PROTOCOL)


class PickleGroup(StorageGroup):
    def __init__(self, data: dict) -> None:
        self.data = data

    def __contains__(self, item: object) -> bool:
        return item in self.data

    def __delitem__(self, key: str) -> None:
        del self.data[key]

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def create_group(self, key: str) -> PickleGroup:
        if key in self.data:
            raise KeyError(f"{key} already exists")
        self.data[key] = {}
        return PickleGroup(self.data[key])

    def require_group(self, key: str) -> PickleGroup:
        return PickleGroup(self.data[key])

    def is_group(self, key: str) -> bool:
        return isinstance(self.get(key, None), dict)
