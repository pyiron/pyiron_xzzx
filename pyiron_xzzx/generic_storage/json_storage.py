from __future__ import annotations

import json
from dataclasses import is_dataclass
from typing import Any

from pyiron_xzzx.generic_storage.dataclass_helpers import unwrap_dataclass
from pyiron_xzzx.generic_storage.interface import GenericStorage, StorageGroup
from pyiron_xzzx.obj_reconstruction.util import get_type, recreate_obj


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
        if isinstance(self.data[key], dict):
            group = JSONGroup(self.data[key])
            type = group.get("_type", "group")
            if type != "group":
                module, qualname, version = type.split("@")
                return recreate_obj(
                    module,
                    qualname,
                    version,
                    init_args={k: v for k, v in group.items() if k != "_type"},
                )
            return group

        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        if is_dataclass(value):
            group = self.create_group(key)
            module, qualname, version = get_type(value)
            group["_type"] = "@".join([module, qualname, version])
            unwrap_dataclass(group, value)
            return

        import numpy

        if isinstance(value, numpy.ndarray):
            group = self.create_group(key)
            module, qualname, version = get_type(value)
            group["_type"] = "@".join(
                [module, qualname.replace("ndarray", "array"), version]
            )
            group["object"] = value.tolist()
            return

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
