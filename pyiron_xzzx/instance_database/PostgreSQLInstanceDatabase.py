from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import JSONB, insert

from .InstanceDatabase import InstanceDatabase


class PostgreSQLInstanceDatabase(InstanceDatabase):
    def __init__(self, connection_string: str, echo: bool = False) -> None:
        self.metadata = MetaData()
        self.table = Table(
            "nodes",
            self.metadata,
            Column("hash", String, primary_key=True),
            Column("qualname", String, nullable=True),
            Column("module", String, nullable=True),
            Column("version", String, nullable=True),
            Column("connected_inputs", JSONB, nullable=True),
            Column("inputs", JSONB, nullable=True),
            Column("outputs", JSONB, nullable=True),
            Column("output_path", String, nullable=True),
        )

        self.engine = create_engine(connection_string, echo=echo)

    def create_table(self) -> None:
        self.metadata.create_all(self.engine)

    def drop_table(self) -> None:
        self.metadata.drop_all(self.engine)

    def create(
        self,
        node: InstanceDatabase.NodeData,
    ) -> str:
        with self.engine.connect() as connection:
            stmt = (
                insert(self.table)
                .values(
                    hash=node.hash,
                    qualname=node.qualname,
                    module=node.module,
                    version=node.version,
                    connected_inputs=node.connected_inputs,
                    inputs=node.inputs,
                    outputs=node.outputs,
                    output_path=node.output_path,
                )
                .on_conflict_do_nothing()
            )
            result = connection.execute(stmt)
            connection.commit()
            return result.inserted_primary_key[0]

    def read(self, hash: str) -> InstanceDatabase.NodeData | None:
        with self.engine.connect() as connection:
            stmt = self.table.select().where(self.table.c.hash == hash)
            result = connection.execute(stmt).first()
            return None if result is None else self.NodeData(**result._mapping)

    def update(self, hash: str, **kwargs) -> None:
        with self.engine.connect() as connection:
            stmt = self.table.update().where(self.table.c.hash == hash).values(**kwargs)
            connection.execute(stmt)

    def delete(self, hash: str) -> None:
        with self.engine.connect() as connection:
            stmt = self.table.delete().where(self.table.c.hash == hash)
            connection.execute(stmt)
