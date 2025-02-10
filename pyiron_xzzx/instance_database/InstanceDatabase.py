from __future__ import annotations

import abc
from dataclasses import dataclass


class InstanceDatabase(abc.ABC):
    @dataclass
    class NodeData:
        hash: str
        label: str
        qualname: str
        module: str
        version: str
        connected_inputs: dict
        inputs: dict
        outputs: list[str]
        output_path: str

    @abc.abstractmethod
    def create_table(self):
        pass

    @abc.abstractmethod
    def drop_table(self):
        pass

    @abc.abstractmethod
    def create(self, node: NodeData) -> str:
        pass

    @abc.abstractmethod
    def read(self, hash: str) -> NodeData | None:
        pass

    @abc.abstractmethod
    def update(self, hash: str, **kwargs):
        pass

    @abc.abstractmethod
    def delete(self, hash: str):
        pass
