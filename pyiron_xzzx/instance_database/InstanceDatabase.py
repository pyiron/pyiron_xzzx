from __future__ import annotations

import abc
from dataclasses import dataclass


class InstanceDatabase(abc.ABC):
    @dataclass
    class NodeData:
        hash: str
        qualname: str
        module: str
        version: str
        connected_inputs: list[str]
        inputs: dict[str, str]
        outputs: list[str]
        output_path: str | None

    @abc.abstractmethod
    def create_table(self) -> None:
        pass

    @abc.abstractmethod
    def drop_table(self) -> None:
        pass

    @abc.abstractmethod
    def create(self, node: NodeData) -> str:
        pass

    @abc.abstractmethod
    def read(self, hash: str) -> NodeData | None:
        pass

    @abc.abstractmethod
    def update(self, hash: str, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def delete(self, hash: str) -> None:
        pass
