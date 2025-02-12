import doctest
import unittest

from pyiron_workflow import Workflow

from pyiron_xzzx.instance_database import (
    PostgreSQLInstanceDatabase,
    get_hash,
    restore_node_from_database,
    store_node_in_database,
)


@Workflow.wrap.as_function_node()
def AddNode(x: int = 1, y: int = 2) -> tuple[int, int]:
    a = x + y
    b = x - y
    return a, b


class TestPostgreSQL(unittest.TestCase):
    def test_node_store_restore(self) -> None:
        node = AddNode(3, 4)

        db = PostgreSQLInstanceDatabase(
            "postgresql://pyiron:pyiron@postgres/pyiron_workflow"
        )
        db.drop_table()
        db.create_table()

        hash = store_node_in_database(
            db, node, store_outputs=False, store_input_nodes_recursively=True
        )

        node_restored = restore_node_from_database(db, hash)
        node_restored.run()
        self.assertEqual(node_restored.output.a, 7)
        self.assertEqual(node_restored.output.a, -1)


if __name__ == "__main__":
    unittest.main()
