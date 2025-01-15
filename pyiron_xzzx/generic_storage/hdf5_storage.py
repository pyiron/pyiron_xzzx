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

        try:
            self.data[key] = value
        except TypeError as type_error:
            raise TypeError(
                f"'{key}' of type {type(value)} cannot be written to HDF5."
            ) from type_error

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def create_group(self, key: str) -> HDF5Group:
        return self.data.create_group(key)

    def require_group(self, key: str) -> HDF5Group:
        return self.data.require_group(key)
