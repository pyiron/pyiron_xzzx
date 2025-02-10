from typing import Any


def get_type(cls: Any) -> tuple[str, str, str]:
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


def recreate_type(module_name: str, qualname: str, version: str, strict_version_check: bool) -> Any:
    from importlib import import_module

    base_module = import_module(module_name.split(".")[0])
    if strict_version_check:
        actual_version = (
            base_module.__version__
            if hasattr(base_module, "__version__")
            else "not_defined"
        )
        if actual_version != version:
            raise ValueError(f"Version mismatch: {version} != {actual_version}")
    module = import_module(module_name)
    recreated_type = getattr(module, qualname)
    return recreated_type


def recreate_obj(module: str, qualname: str, version: str, init_args: dict[str, Any]) -> Any:
    recreated_type = recreate_type(module, qualname, version)
    obj = recreated_type(**init_args)
    return obj
