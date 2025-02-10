from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any, Iterator

import h5py

from pyiron_xzzx.generic_storage.interface import GenericStorage, StorageGroup
from pyiron_xzzx.generic_storage.dataclass_helpers import unwrap_dataclass
from pyiron_xzzx.obj_reconstruction.util import get_type, recreate_obj


class HDF5Storage(GenericStorage):
    def __init__(self, filename: str, mode="r"):
        super().__init__()
        self.file = h5py.File(filename, mode)
        self.data = self.file

    def _close(self):
        self.file.close()

    def __enter__(self) -> HDF5Group:
        return HDF5Group(self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()


class HDF5Group(StorageGroup):
    def __init__(self, data: h5py.File):
        self.data = data

    def __contains__(self, item: object) -> bool:
        return item in self.data

    def __delitem__(self, key: str):
        del self.data[key]

    def __getitem__(self, key: str) -> Any:
        if self.is_group(key):
            group = HDF5Group(self.data[key])
            type = group.get("_type", "group")
            match type:
                case "group":
                    return group
                case "None":
                    return None
                case "list":
                    lst = []
                    i = 0
                    while f"item_{i}" in group:
                        lst.append(group[f"item_{i}"])
                        i += 1
                    return lst
                case _:
                    return self._recover_value(group)

        value = self.data[key]

        # scalar
        if value.ndim == 0:
            if h5py.check_string_dtype(value.dtype):
                return value.asstr()[()]
            return value[()]

        # array
        return value[:]

    def __setitem__(self, key: str, value: Any):
        if value is None:
            group = self.create_group(key)
            group["_type"] = "None"
            return

        if isinstance(value, list):
            group = self.create_group(key)
            group["_type"] = "list"
            for i, v in enumerate(value):
                group[f"item_{i}"] = v
            return

        self._transform_value(key, value)

        if key not in self:
            self.data[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def create_group(self, key: str) -> HDF5Group:
        return HDF5Group(self.data.create_group(key))

    def require_group(self, key: str) -> HDF5Group:
        return HDF5Group(self.data.require_group(key))

    def is_group(self, key: str) -> bool:
        return self.data.get(key, getclass=True) is h5py.Group
