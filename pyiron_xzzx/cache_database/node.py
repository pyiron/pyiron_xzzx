import hashlib
import json
from typing import Any

from pyiron_xzzx.cache_database.cache_database import CacheDatabase
from pyiron_xzzx.generic_storage import HDF5Storage
from pyiron_workflow.node import Node
from pyiron_workflow.workflow import Workflow


def store_node_outputs(node: Node) -> str:
    """
    Store a node's outputs into an HDF5 file.

    Args:
        node (Node): The node whose outputs should be stored.

    Returns:
        str: The file path where the node's outputs are stored.
    """
    node_hash = get_node_hash(node_to_dict(node))
    output_path = f".storage/{node_hash}.hdf5"
    with HDF5Storage(output_path, "w") as storage:
        for k, v in node.outputs.items():
            storage[k] = v.value
    return output_path


def restore_node_outputs(node: Node) -> bool:
    """
    Restore a node's outputs from a stored HDF5 file, given by node.hash.

    Args:
        node: the node whose outputs should be restored.

    Returns:
        True if the outputs were restored, False if not.
    """

    node_hash = get_node_hash(node_to_dict(node))
    output_path = f".storage/{node_hash}.hdf5"
    with HDF5Storage(output_path, "r") as storage:
        for k, v in storage.items():
            node.outputs[k].value = node.outputs[k].type_hint(v)
    return True


def get_type(cls):
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


def recreate_node(module: str, qualname: str, version: str, label: str) -> Node:
    from importlib import import_module

    base_module = import_module(module)
    actual_version = (
        base_module.__version__
        if hasattr(base_module, "__version__")
        else "not_defined"
    )
    if actual_version != version:
        raise ValueError(f"Version mismatch: {version} != {actual_version}")
    node = getattr(base_module, qualname)(label=label)
    return node


def node_to_dict(node: Node) -> dict:
    module, qualname, version = get_type(node)
    connected_inputs = [input.label for input in node.inputs if input.connected]
    node_dict = {
        "inputs": node_inputs_to_dict(node),
        "node": {
            "qualname": qualname,
            "module": module,
            "version": version,
            "connected_inputs": connected_inputs,
        },
    }
    return node_dict


def get_node_hash(obj_to_be_hashed: Node | dict) -> str:
    node_dict = (
        obj_to_be_hashed
        if isinstance(obj_to_be_hashed, dict)
        else node_to_dict(obj_to_be_hashed)
    )
    jsonified_dict = json.dumps(node_dict, sort_keys=True)

    hasher = hashlib.sha256()
    hasher.update(jsonified_dict.encode("utf-8"))
    hash_value = hasher.hexdigest()

    return hash_value


def node_inputs_to_dict(node: Node) -> dict[str, Any]:
    def resolve_connections(value: Any):
        if value.connected:
            return (
                get_node_hash(value.connections[0].owner)
                + "@"
                + value.connections[0].label
            )
        else:
            return str(value)

    output = {k: resolve_connections(v) for k, v in node.inputs.items()}

    return output


def node_outputs_to_dict(node: Node) -> dict[str, Any]:
    output = {k: v.value for k, v in node.outputs.items()}
    return output


def store_node_in_database(
    db: CacheDatabase,
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
        db (CacheDatabase): The database to store the node in.
        node (Node): The node to store.
        store_outputs (bool): Whether to store the outputs of the node as well.
        store_input_nodes_recursively (bool): Whether to store all the nodes that are
            connected to the inputs of the node recursively.

    Returns:
        str: The hash of the stored node.
    """
    node_dict = node_to_dict(node)
    node_hash = get_node_hash(node_dict)
    output_path = None
    if store_outputs:
        output_path = store_node_outputs(node)

    db.create(
        hash=node_hash,
        label=node.label,
        qualname=node_dict["node"]["qualname"],
        module=node_dict["node"]["module"],
        version=node_dict["node"]["version"],
        connected_inputs=node_dict["node"]["connected_inputs"],
        inputs=node_dict["inputs"],
        output_path=output_path,
    )
    if store_input_nodes_recursively:
        connected_nodes = [
            input.connections[0].owner for input in node.inputs if input.connected
        ]
        for node in connected_nodes:
            store_node_in_database(
                db,
                node,
                store_outputs=store_outputs,
                store_input_nodes_recursively=store_input_nodes_recursively,
            )
    return node_hash


def restore_node_from_database(
    db: CacheDatabase, node_hash: str, parent: Workflow
) -> Node:
    """
    Restore a node from the database.

    The node is reconstructed from the database by calling recreate_node and
    adding it to the given parent workflow. The node's inputs are then restored
    either by connecting them to other nodes in the workflow or by setting their
    values directly.

    Args:
        db: The CacheDatabase instance to read from.
        node_hash: The hash of the node to restore.
        parent: The workflow to add the restored node to.

    Returns:
        The restored node.
    """
    # restore node
    db_result = db.read(node_hash)

    node = recreate_node(
        module=db_result.module,
        qualname=db_result.qualname,
        version=db_result.version,
        label=db_result.label,
    )
    parent.add_child(node)

    # restore inputs
    for k, v in db_result.inputs.items():
        if k in db_result.connected_inputs:
            input_hash, input_label = v.split("@")
            input_node = restore_node_from_database(db, input_hash, parent)
            node.inputs[k].connect(input_node.outputs[input_label])
        else:
            node.inputs[k] = node.inputs[k].type_hint(v)

    return node
