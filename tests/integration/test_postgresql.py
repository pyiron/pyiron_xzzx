import doctest
import unittest

from pyiron_workflow import Workflow

from pyiron_xzzx.instance_database import (
    PostgreSQLInstanceDatabase,
    get_hash,
    restore_node_from_database,
    store_node_in_database,
)


class TestPostgreSQL(unittest.TestCase):

    def test_node_store_restore(self) -> None:
        @Workflow.wrap.as_function_node()
        def AddNode(x: int = 1, y: int = 2) -> tuple[int, int]:
            a = x + y
            b = x - y
            return a, b

        node = AddNode(3, 4)

        db = PostgreSQLInstanceDatabase(
            "postgresql://pyiron:pyiron@postgres/pyiron_workflow"
        )
        db.drop_table()
        db.create_table()

        print("hash: ", get_hash(node))

        hash = store_node_in_database(
            db, node, store_outputs=False, store_input_nodes_recursively=True
        )
        print("hash: ", hash)

        wf2 = Workflow("wf2")
        node_restored = restore_node_from_database(db, hash, wf2)
        node_restored.run()
        self.assertEqual(node_restored.output, (7, -1))


if __name__ == "__main__":
    unittest.main()
