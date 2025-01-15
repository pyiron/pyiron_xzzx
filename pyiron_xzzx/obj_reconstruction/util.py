from typing import Any


def get_type(cls):
    module = cls.__class__.__module__
    qualname = cls.__class__.__qualname__
    from importlib import import_module

    base_module = import_module(module.split(".")[0])
    version = (
        base_module.__version__
        if hasattr(base_module, "__version__")
        else "not_defined"
    )
    return module, qualname, version


def recreate_obj(module: str, qualname: str, version: str, init_args: dict) -> Any:
    from importlib import import_module

    base_module = import_module(module.split(".")[0])
    actual_version = (
        base_module.__version__
        if hasattr(base_module, "__version__")
        else "not_defined"
    )
    if actual_version != version:
        raise ValueError(f"Version mismatch: {version} != {actual_version}")
    module = import_module(module)
    obj = getattr(module, qualname)(**init_args)
    return obj
