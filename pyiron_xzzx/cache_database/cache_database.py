from __future__ import annotations

from dataclasses import dataclass
import enum

from sqlalchemy import Column, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import JSONB


class OutputState(enum.Enum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    IN_DATABASE = "IN_DATABASE"
    EXTERNAL = "EXTERNAL"


class CacheDatabase:
    @dataclass
    class NodeData:
        hash: str
        label: str
        qualname: str
        module: str
        version: str
        connected_inputs: dict
        inputs: dict
        output_path: str
        
    def __init__(self, connection_string: str, echo: bool = False):
        self.metadata = MetaData()
        self.table = Table(
            "nodes",
            self.metadata,
            Column("hash", String, primary_key=True),
            Column("label", String, nullable=True),
            Column("qualname", String, nullable=True),
            Column("module", String, nullable=True),
            Column("version", String, nullable=True),
            Column("connected_inputs", JSONB, nullable=True),
            Column("inputs", JSONB, nullable=True),
            Column("output_path", String, nullable=True),
        )

        self.engine = create_engine(connection_string, echo=echo)

    def create_table(self):
        self.metadata.create_all(self.engine)

    def drop_table(self):
        self.metadata.drop_all(self.engine)

    def create(
        self,
        node: NodeData,
    ) -> str:
        if self.read(node.hash) is not None:
            return node.hash

        with self.engine.connect() as connection:
            stmt = self.table.insert().values(
                hash=node.hash,
                label=node.label,
                qualname=node.qualname,
                module=node.module,
                version=node.version,
                connected_inputs=node.connected_inputs,
                inputs=node.inputs,
                output_path=node.output_path,
            )
            result = connection.execute(stmt)
            connection.commit()
            return result.inserted_primary_key[0]

    def read(self, hash: str) -> NodeData | None:
        with self.engine.connect() as connection:
            stmt = self.table.select().where(self.table.c.hash == hash)
            result = connection.execute(stmt).first()
            return None if result is None else self.NodeData(**result._mapping)

    def update(self, hash: str, **kwargs):
        with self.engine.connect() as connection:
            stmt = self.table.update().where(self.table.c.hash == hash).values(**kwargs)
            connection.execute(stmt)

    def delete(self, hash: str):
        with self.engine.connect() as connection:
            stmt = self.table.delete().where(self.table.c.hash == hash)
            connection.execute(stmt)
