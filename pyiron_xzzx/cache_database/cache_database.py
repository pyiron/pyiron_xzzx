from __future__ import annotations

import enum

from sqlalchemy import Column, Enum, Integer, MetaData, String, Table, create_engine
from sqlalchemy.dialects.postgresql import JSONB


class OutputState(enum.Enum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    IN_DATABASE = "IN_DATABASE"
    EXTERNAL = "EXTERNAL"


class CacheDatabase:
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
        hash: str,
        label: str | None,
        qualname,
        module,
        version,
        connected_inputs,
        inputs,
        output_path,
    ) -> str:
        if self.read(hash) is not None:
            raise ValueError("A node with this hash already exists in the database!")

        with self.engine.connect() as connection:
            stmt = self.table.insert().values(
                hash=hash,
                label=label,
                qualname=qualname,
                module=module,
                version=version,
                connected_inputs=connected_inputs,
                inputs=inputs,
                output_path=output_path,
            )
            result = connection.execute(stmt)
            connection.commit()
            return result.inserted_primary_key[0]

    def read(self, hash: str):
        with self.engine.connect() as connection:
            stmt = self.table.select().where(self.table.c.hash == hash)
            result = connection.execute(stmt)
            return result.first()

    def update(self, hash, **kwargs):
        with self.engine.connect() as connection:
            stmt = self.table.update().where(self.table.c.hash == hash).values(**kwargs)
            connection.execute(stmt)

    def delete(self, hash: str):
        with self.engine.connect() as connection:
            stmt = self.table.delete().where(self.table.c.hash == hash)
            connection.execute(stmt)
