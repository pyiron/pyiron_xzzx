from __future__ import annotations
import pickle
from typing import Any

from pyiron_xzzx.generic_storage.interface import GenericStorage, StorageGroup


class PickleStorage(GenericStorage):
    def __init__(self, filename: str, mode="rb"):
        super().__init__()
        self.file = open(filename, mode)
        self.data: dict = {}

    def _close(self):
        self.file.close()

    def __enter__(self) -> PickleGroup:
        if self.file.readable():
            self.data = pickle.load(self.file)

        return PickleGroup(self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.file.writable():
            pickle.dump(self.data, self.file, pickle.HIGHEST_PROTOCOL)
        self._close()


class PickleGroup(StorageGroup):
    def __init__(self, data: dict):
        self.data = data

    def __contains__(self, item: object):
        return item in self.data

    def __delitem__(self, key: str):
        del self.data[key]

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def create_group(self, key: str) -> PickleGroup:
        if key in self.data:
            raise KeyError(f"{key} already exists")
        self.data[key] = {}
        return PickleGroup(self.data[key])

    def require_group(self, key: str) -> PickleGroup:
        return PickleGroup(self.data[key])
