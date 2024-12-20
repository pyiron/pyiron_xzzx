from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any

import h5py

from pyiron_xzzx.generic_storage import GenericStorage, StorageGroup
from pyiron_xzzx.generic_storage.dataclass_helpers import unwrap_dataclass
from pyiron_xzzx.obj_reconstruction.util import get_type, recreate_obj


class HDF5Storage(GenericStorage):
    def __init__(self, filename: str, mode="r"):
        super().__init__()
        self.file = h5py.File(filename, mode)
        self.data = self.file

    def close(self):
        self.file.close()

    def __enter__(self) -> HDF5Group:
        return HDF5Group(self.data)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class HDF5Group(StorageGroup):
    def __init__(self, data: h5py.File):
        self.data = data

    def __contains__(self, item: object):
        return item in self.data

    def __delitem__(self, key: str):
        del self.data[key]

    def __getitem__(self, key: str) -> Any:
        if self.data.get(key, getclass=True) is h5py.Group:
            group = HDF5Group(self.data[key])
            type = group.get("_type", "group")
            if type != "group":
                module, qualname, version = type.split("@")
                return recreate_obj(
                    module,
                    qualname,
                    version,
                    init_args={k: v for k, v in group.items() if k != "_type"},
                )
            return HDF5Group(self.data[key])

        value = self.data[key]

        # scalar
        if value.ndim == 0:
            if h5py.check_string_dtype(self.data[key].dtype):
                return self.data[key].asstr()[()]
            return self.data[key][()]

        # array
        return self.data[key][:]

    def __setitem__(self, key: str, value: Any):
        if is_dataclass(value):
            group = HDF5Group(self.create_group(key))
            module, qualname, version = get_type(value)
            group["_type"] = "@".join([module, qualname, version])
            unwrap_dataclass(group, value)
            return

        self.data[key] = value

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def create_group(self, key: str) -> HDF5Group:
        return self.data.create_group(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.data:
            return self[key]
        return default

    def require_group(self, key: str) -> HDF5Group:
        return self.data.require_group(key)
