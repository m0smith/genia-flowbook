"""
Genia-owned Flowbook workflow runner.

This module owns the minimal in-repo pipeline/workflow semantics used by the
Flowbook notebook executor while the broader Genia runtime transport is still
under construction.
"""

from collections import deque
from typing import Any, Callable, Dict, List, Optional, Tuple


WorkflowResult = Dict[str, Any]
OperationFn = Callable[[List[Any], Any], List[Any]]

SUPPORTED_OPERATIONS = ("input", "inc", "map", "sum")


def list_supported_operations() -> List[str]:
    """Return the MVP operation names supported by the local workflow runner."""
    return list(SUPPORTED_OPERATIONS)


def execute_workflow(workflow: Any, input_val: Any = None) -> WorkflowResult:
    """
    Execute a workflow-shaped pipeline and return a normalized interpreter result.

    Result shape is always:
    {
        "success": bool,
        "output": list,
        "error": str | None,
        "nodeOutputs": { [node_id]: list }
    }
    """
    try:
        normalized_workflow = _normalize_workflow(workflow)
        node_order = _topological_order(normalized_workflow)
        node_outputs = _execute_nodes(normalized_workflow, node_order, input_val)
        terminal_outputs = _collect_terminal_outputs(normalized_workflow, node_outputs)
        return _result(
            success=True,
            output=terminal_outputs,
            error=None,
            node_outputs=node_outputs,
        )
    except WorkflowValidationError as exc:
        return _result(success=False, error=str(exc))
    except WorkflowExecutionError as exc:
        return _result(success=False, error=str(exc))
    except Exception as exc:  # pragma: no cover - defensive guard
        return _result(success=False, error=f"Workflow execution failed: {exc}")


class WorkflowValidationError(ValueError):
    """Workflow data failed validation."""


class WorkflowExecutionError(RuntimeError):
    """Workflow execution failed at runtime."""


def _normalize_workflow(workflow: Any) -> Dict[str, Any]:
    if not isinstance(workflow, dict):
        raise WorkflowValidationError("Invalid workflow shape: workflow must be an object.")

    nodes = workflow.get("nodes")
    edges = workflow.get("edges")

    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise WorkflowValidationError(
            "Invalid workflow shape: workflow must contain 'nodes' and 'edges' arrays."
        )

    node_ids = set()
    normalized_nodes: List[Dict[str, Any]] = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise WorkflowValidationError(
                f"Invalid workflow shape: node at index {index} must be an object."
            )

        node_id = node.get("id")
        operation = node.get("operation")
        if not isinstance(node_id, str) or not node_id:
            raise WorkflowValidationError(
                f"Invalid workflow shape: node at index {index} must have a string 'id'."
            )
        if node_id in node_ids:
            raise WorkflowValidationError(f"Duplicate node ID '{node_id}'.")
        if not isinstance(operation, str) or not operation:
            raise WorkflowValidationError(
                f"Invalid workflow shape: node '{node_id}' must have a string 'operation'."
            )
        if operation not in SUPPORTED_OPERATIONS:
            raise WorkflowValidationError(f"Unknown operation '{operation}'.")

        node_ids.add(node_id)
        normalized_nodes.append(
            {
                "id": node_id,
                "operation": operation,
                "index": index,
            }
        )

    normalized_edges: List[Dict[str, str]] = []
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise WorkflowValidationError(
                f"Invalid workflow shape: edge at index {index} must be an object."
            )

        from_node = edge.get("from")
        to_node = edge.get("to")
        if not isinstance(from_node, str) or not isinstance(to_node, str):
            raise WorkflowValidationError(
                f"Invalid workflow shape: edge at index {index} must have string 'from' and 'to'."
            )
        if from_node not in node_ids or to_node not in node_ids:
            raise WorkflowValidationError(
                f"Dangling edge from '{from_node}' to '{to_node}'."
            )
        normalized_edges.append({"from": from_node, "to": to_node})

    return {"nodes": normalized_nodes, "edges": normalized_edges}


def _topological_order(workflow: Dict[str, Any]) -> List[str]:
    nodes = workflow["nodes"]
    edges = workflow["edges"]
    node_index = {node["id"]: node["index"] for node in nodes}
    adjacency: Dict[str, List[str]] = {node["id"]: [] for node in nodes}
    in_degree: Dict[str, int] = {node["id"]: 0 for node in nodes}

    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda candidate: node_index[candidate])

    queue = deque(
        sorted(
            (node["id"] for node in nodes if in_degree[node["id"]] == 0),
            key=lambda candidate: node_index[candidate],
        )
    )
    order: List[str] = []

    while queue:
        node_id = queue.popleft()
        order.append(node_id)

        for child_id in adjacency[node_id]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                queue.append(child_id)

    if len(order) != len(nodes):
        raise WorkflowValidationError("Cycle detected in workflow graph.")

    return order


def _execute_nodes(
    workflow: Dict[str, Any],
    order: List[str],
    input_val: Any,
) -> Dict[str, List[Any]]:
    nodes = {node["id"]: node for node in workflow["nodes"]}
    parents: Dict[str, List[Tuple[int, str]]] = {node_id: [] for node_id in nodes}

    for edge in workflow["edges"]:
        parent_index = nodes[edge["from"]]["index"]
        parents[edge["to"]].append((parent_index, edge["from"]))

    for node_id in parents:
        parents[node_id].sort(key=lambda item: item[0])

    node_outputs: Dict[str, List[Any]] = {}
    for node_id in order:
        node = nodes[node_id]
        upstream_outputs: List[Any] = []
        for _, parent_id in parents[node_id]:
            upstream_outputs.extend(node_outputs[parent_id])

        operation = _operation_for(node["operation"])
        try:
            node_outputs[node_id] = _normalize_output(
                operation(upstream_outputs, input_val)
            )
        except WorkflowExecutionError:
            raise
        except Exception as exc:
            raise WorkflowExecutionError(
                f"Runtime error while executing node '{node_id}' ({node['operation']}): {exc}"
            ) from exc

    return node_outputs


def _collect_terminal_outputs(
    workflow: Dict[str, Any],
    node_outputs: Dict[str, List[Any]],
) -> List[Any]:
    parent_ids = {edge["from"] for edge in workflow["edges"]}
    terminal_nodes = [
        node["id"]
        for node in sorted(workflow["nodes"], key=lambda item: item["index"])
        if node["id"] not in parent_ids
    ]

    final_output: List[Any] = []
    for node_id in terminal_nodes:
        final_output.extend(node_outputs.get(node_id, []))
    return final_output


def _operation_for(name: str) -> OperationFn:
    operations: Dict[str, OperationFn] = {
        "input": _op_input,
        "inc": _op_inc,
        "map": _op_map,
        "sum": _op_sum,
    }
    return operations[name]


def _op_input(_upstream: List[Any], input_val: Any) -> List[Any]:
    return _normalize_output(input_val)


def _op_inc(upstream: List[Any], _input_val: Any) -> List[Any]:
    if not upstream:
        return []

    incremented: List[Any] = []
    for value in upstream:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise WorkflowExecutionError(
                f"Operation 'inc' requires numeric input, got {type(value).__name__}."
            )
        incremented.append(value + 1)
    return incremented


def _op_map(upstream: List[Any], _input_val: Any) -> List[Any]:
    mapped: List[Any] = []
    for value in upstream:
        if isinstance(value, list):
            mapped.extend(value)
        else:
            mapped.append(value)
    return mapped


def _op_sum(upstream: List[Any], _input_val: Any) -> List[Any]:
    total = 0
    for value in upstream:
        if isinstance(value, list):
            for inner in value:
                total += _as_number(inner, "sum")
        else:
            total += _as_number(value, "sum")
    return [total]


def _as_number(value: Any, operation: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise WorkflowExecutionError(
            f"Operation '{operation}' requires numeric input, got {type(value).__name__}."
        )
    return value


def _normalize_output(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _result(
    success: bool,
    output: Optional[List[Any]] = None,
    error: Optional[str] = None,
    node_outputs: Optional[Dict[str, List[Any]]] = None,
) -> WorkflowResult:
    return {
        "success": success,
        "output": output if isinstance(output, list) else [],
        "error": error if error else None,
        "nodeOutputs": node_outputs if isinstance(node_outputs, dict) else {},
    }
