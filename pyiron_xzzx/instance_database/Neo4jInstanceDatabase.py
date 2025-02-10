from __future__ import annotations

from neo4j import GraphDatabase

from .InstanceDatabase import InstanceDatabase


class Neo4jInstanceDatabase(InstanceDatabase):
    def __init__(self, uri, auth):
        self.uri = uri
        self.auth = auth
        self.driver = GraphDatabase.driver(self.uri, auth=self.auth)

    def close(self) -> None:
        self.driver.close()

    def create_table(self) -> None:
        with self.driver.session() as session:
            session.run(
                "CREATE INDEX node_hash_index IF NOT EXISTS FOR (n:NODE) ON (n.hash)"
            )

    def drop_table(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create(
        self,
        node: InstanceDatabase.NodeData,
    ) -> str:
        with self.driver.session(database="neo4j") as tx:
            inp = [{"key": k, "value": v} for k, v in node.inputs.items()]
            out = [{"key": k} for k in node.outputs]
            channels = [
                {
                    "input_channel": input_channel,
                    "output_hash": node.inputs[input_channel].split("@")[0],
                    "output_channel": node.inputs[input_channel].split("@")[1],
                }
                for input_channel in node.connected_inputs
            ]
            tx.run(
                """
                MERGE (n :NODE {hash: $hash, name:$name, module:$module, version:$version, output_path:$output_path})

                WITH n, $inp AS inp
                UNWIND inp AS input
                MERGE (:INPUT {key:input.key, value:input.value}) -[:INPUT]-> (n)

                WITH n, $out AS out
                UNWIND out AS output
                MERGE (:OUTPUT {key:output.key}) <-[:OUTPUT]- (n)

                WITH n AS input_node, $channels AS channels
                UNWIND channels AS channel
                MATCH (output_node:NODE {hash: channel.output_hash}) -[:OUTPUT]-> (o:OUTPUT {key:channel.output_channel})
                MATCH (input_node) <-[:INPUT]- (i:INPUT {key:channel.input_channel})
                MERGE (o)-[:CONNECTION]->(i)
                """,
                hash=node.hash,
                name=node.qualname,
                module=node.module,
                version=node.version,
                output_path=node.output_path if node.output_path else "",
                inp=inp,
                out=out,
                channels=channels,
            )
        return node.hash

    def read(self, hash: str) -> InstanceDatabase.NodeData | None:
        with GraphDatabase.driver(self.uri, auth=self.auth) as driver:
            records, summary, keys = driver.execute_query(
                """
            MATCH (i) --> (n {hash:$hash}) --> (o)
            RETURN n, o, i
            """,
                hash=hash,
            )

        node = records[0].data()["n"]
        inputs = {rec.data()["i"]["key"]: rec.data()["i"]["value"] for rec in records}
        connected_inputs = [
            k for k, v in inputs.items() if isinstance(v, str) and "@" in v
        ]
        outputs = list({rec.data()["o"]["key"] for rec in records})

        res = self.NodeData(
            hash=node["hash"],
            qualname=node["name"],
            module=node["module"],
            version=node["version"],
            connected_inputs=connected_inputs,
            inputs=inputs,
            outputs=outputs,
            output_path=node["output_path"],
        )
        return res

    def update(self, hash: str, **kwargs):
        raise NotImplementedError

    def delete(self, hash: str):
        raise NotImplementedError
