from __future__ import annotations

import abc
import contextlib
from collections.abc import MutableMapping
from typing import Any

from pyiron_xzzx.obj_reconstruction.util import recreate_type


class StorageGroup(MutableMapping[str, Any], abc.ABC):
    """API for organizing/loading/storing stuff"""

    @abc.abstractmethod
    def create_group(self, key: str) -> StorageGroup:
        pass

    @abc.abstractmethod
    def require_group(self, key: str) -> StorageGroup:
        pass

    @abc.abstractmethod
    def is_group(self, key: str) -> bool:
        pass

    def _recover_value(self, group: StorageGroup) -> Any:
        type = group.get("_type", "group")
        match type:
            case "group":
                return group
            case "type":
                module, qualname, version = group["_class"].split("@")
                return recreate_type(
                    module,
                    qualname,
                    version,
                )
            case "pickle":
                func = group["func"]
                args = group["args"]
                obj = func(*args)
                state = group["state"]
                if hasattr(obj, "__setstate__"):
                    obj.__setstate__(state)
                else:
                    obj.__dict__.update(**state)
                return obj
            case "tuple":
                lst = []
                i = 0
                while f"item_{i}" in group:
                    lst.append(group[f"item_{i}"])
                    i += 1
                return tuple(lst)
            case "global":
                module, qualname, version = group["_class"].split("@")
                return recreate_type(
                    module,
                    qualname,
                    version,
                )
            case "base64":
                from base64 import b64decode

                return b64decode(group["value"].encode("utf8"))
            case _:
                raise TypeError(f"Could not instantiate: {type}")

    def _transform_value(self, key: str, value: Any) -> None:
        if isinstance(value, type) or callable(value):
            module, qualname, version = (
                value.__module__,
                value.__qualname__,
                "not_defined",
            )
            group = self.create_group(key)
            group["_type"] = "type"
            group["_class"] = "@".join([module, qualname, version])
            return

        if isinstance(value, tuple):
            group = self.create_group(key)
            group["_type"] = "tuple"
            for i, v in enumerate(value):
                group[f"item_{i}"] = v
            return

        if isinstance(value, dict):
            group = self.create_group(key)
            for k, v in value.items():
                group[k] = v
            return

        if hasattr(value, "__reduce__"):
            try:
                rv = value.__reduce__()
            except TypeError:
                pass
            else:
                if isinstance(rv, str):
                    module, qualname, version = value.__module__, rv, "not_defined"
                    group = self.create_group(key)
                    group["_type"] = "global"
                    group["_class"] = "@".join([module, qualname, version])
                    return

                func, args, state, *reminder = value.__reduce__()
                group = self.create_group(key)
                group["_type"] = "pickle"
                group["func"] = func
                group["args"] = args
                group["state"] = state
                return

        if isinstance(value, bytes):
            from base64 import b64encode

            group = self.create_group(key)
            group["_type"] = "base64"
            group["value"] = b64encode(value).decode("utf8")
            return
