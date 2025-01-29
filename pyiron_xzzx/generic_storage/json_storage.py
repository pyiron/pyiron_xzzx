from __future__ import annotations

import json
from dataclasses import is_dataclass
from typing import Any

from pyiron_xzzx.generic_storage.dataclass_helpers import unwrap_dataclass
from pyiron_xzzx.generic_storage.interface import GenericStorage, StorageGroup
from pyiron_xzzx.obj_reconstruction.util import get_type, recreate_obj, recreate_type


class JSONStorage(GenericStorage):
    def __init__(self, filename: str, mode="r"):
        super().__init__()
        self.file = open(filename, mode)
        self.data: dict = {}

    def _close(self):
        self.file.close()

    def __enter__(self) -> JSONGroup:
        if self.file.readable():
            self.data = json.loads(self.file.read())

        return JSONGroup(self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.file.writable():
            self.file.write(json.dumps(self.data))
        self._close()


class JSONGroup(StorageGroup):
    def __init__(self, data: dict):
        self.data = data

    def __contains__(self, item: object):
        return item in self.data

    def __delitem__(self, key: str):
        del self.data[key]

    def __getitem__(self, key: str) -> Any:
        if self.is_group(key):
            group = JSONGroup(self.data[key])
            type = group.get("_type", "group")
            match type:
                case "group":
                    return group
                case _:
                    return self._recover_value(group)

        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self._transform_value(key, value)

        if key not in self:
            self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def create_group(self, key: str) -> JSONGroup:
        if key in self.data:
            raise KeyError(f"{key} already exists")
        self.data[key] = {}
        return JSONGroup(self.data[key])

    def require_group(self, key: str) -> JSONGroup:
        return JSONGroup(self.data[key])
    
    def is_group(self, key: str) -> bool:
        return isinstance(self.data.get(key, None), dict)
