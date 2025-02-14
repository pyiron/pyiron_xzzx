# pyiron_module_template

## Instance Database Interface
```python
def store_node_outputs(node: Node) -> str:
    """
    Store a node's outputs into an HDF5 file.

    Args:
        node (Node): The node whose outputs should be stored.

    Returns:
        str: The file path where the node's outputs are stored.

    Raises:
        ValueError: If any output of the node is NOT_DATA.
    """

def restore_node_outputs(node: Node) -> bool:
    """
    Restore a node's outputs from a stored HDF5 file, given by node.hash.

    Args:
        node (Node): the node whose outputs should be restored.

    Returns:
        bool: True if the outputs were restored, False if not.
    """

def store_node_in_database(
    db: InstanceDatabase,
    node: Node,
    store_outputs: bool = False,
    store_input_nodes_recursively: bool = False,
) -> str:
    """
    Store a node in a database.

    This function stores all the information that is required to restore a node from the
    database. This includes the node's class, its inputs, its connected inputs and its
    outputs.

    Args:
        db (InstanceDatabase): The database to store the node in.
        node (Node): The node to store.
        store_outputs (bool): Whether to store the outputs of the node as well.
        store_input_nodes_recursively (bool): Whether to store all the nodes that are
            connected to the inputs of the node recursively.

    Returns:
        str: The hash of the stored node.
    """

def restore_node_from_database(
    db: InstanceDatabase, node_hash: str, parent: Workflow | None = None
) -> Node:
    """
    Restore a node from the database.

    The node is reconstructed from the database by calling recreate_node and
    adding it to the given parent workflow. The node's inputs are then restored
    either by connecting them to other nodes in the workflow or by setting their
    values directly.

    Args:
        db (InstanceDatabase): The InstanceDatabase instance to read from.
        node_hash (str): The hash of the node to restore.
        parent (Workflow | None): The workflow to add the restored node to.

    Returns:
        Node: The restored node.

    Raises:
        RuntimeError: If the node with the given hash is not found in the database.
    """

def get_hash(obj_to_be_hashed: Node | JSONGroup) -> str:
    """
    Calculate the hash of a given node or JSONGroup.

    Args:
        obj_to_be_hashed (Node | JSONGroup): the object whose hash should be calculated.

    Returns:
        str: the SHA-256 hash of the object.
    """
```