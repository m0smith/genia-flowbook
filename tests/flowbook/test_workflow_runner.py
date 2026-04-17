from genia.flowbook.api import execute
from genia.flowbook.workflow import execute_workflow


def test_workflow_runner_executes_simple_pipeline_with_deterministic_node_outputs():
    result = execute_workflow(
        {
            "nodes": [
                {"id": "n1", "operation": "input"},
                {"id": "n2", "operation": "inc"},
                {"id": "n3", "operation": "sum"},
            ],
            "edges": [
                {"from": "n1", "to": "n2"},
                {"from": "n2", "to": "n3"},
            ],
        },
        input_val=[1, 2, 3],
    )

    assert result == {
        "success": True,
        "output": [9],
        "error": None,
        "nodeOutputs": {
            "n1": [1, 2, 3],
            "n2": [2, 3, 4],
            "n3": [9],
        },
    }


def test_workflow_runner_returns_structured_failure_for_duplicate_node_ids():
    result = execute_workflow(
        {
            "nodes": [
                {"id": "n1", "operation": "input"},
                {"id": "n1", "operation": "inc"},
            ],
            "edges": [],
        }
    )

    assert result == {
        "success": False,
        "output": [],
        "error": "Duplicate node ID 'n1'.",
        "nodeOutputs": {},
    }


def test_workflow_runner_returns_structured_failure_for_invalid_workflow_shape():
    result = execute_workflow({"nodes": [{"id": "n1", "operation": "input"}]})

    assert result == {
        "success": False,
        "output": [],
        "error": "Invalid workflow shape: workflow must contain 'nodes' and 'edges' arrays.",
        "nodeOutputs": {},
    }


def test_workflow_runner_returns_structured_failure_for_dangling_edges():
    result = execute_workflow(
        {
            "nodes": [{"id": "n1", "operation": "input"}],
            "edges": [{"from": "n1", "to": "missing"}],
        }
    )

    assert result == {
        "success": False,
        "output": [],
        "error": "Dangling edge from 'n1' to 'missing'.",
        "nodeOutputs": {},
    }


def test_workflow_runner_returns_structured_failure_for_cycles():
    result = execute_workflow(
        {
            "nodes": [
                {"id": "n1", "operation": "input"},
                {"id": "n2", "operation": "inc"},
            ],
            "edges": [
                {"from": "n1", "to": "n2"},
                {"from": "n2", "to": "n1"},
            ],
        }
    )

    assert result == {
        "success": False,
        "output": [],
        "error": "Cycle detected in workflow graph.",
        "nodeOutputs": {},
    }


def test_workflow_runner_returns_structured_failure_for_unknown_operations():
    result = execute_workflow(
        {
            "nodes": [{"id": "n1", "operation": "mystery"}],
            "edges": [],
        }
    )

    assert result == {
        "success": False,
        "output": [],
        "error": "Unknown operation 'mystery'.",
        "nodeOutputs": {},
    }


def test_workflow_runner_returns_structured_failure_for_runtime_errors():
    result = execute_workflow(
        {
            "nodes": [
                {"id": "n1", "operation": "input"},
                {"id": "n2", "operation": "inc"},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
        input_val=["hello"],
    )

    assert result == {
        "success": False,
        "output": [],
        "error": "Operation 'inc' requires numeric input, got str.",
        "nodeOutputs": {},
    }


def test_default_notebook_execution_uses_local_workflow_runner():
    result = execute(
        {
            "version": "1.0.0",
            "cells": [
                {
                    "id": "p1",
                    "type": "pipeline_cell",
                    "pipeline": {
                        "nodes": [
                            {"id": "n1", "type": "source", "operation": "input"},
                            {"id": "n2", "type": "transform", "operation": "inc"},
                            {"id": "n3", "type": "sink", "operation": "sum"},
                        ],
                        "edges": [
                            {"id": "e1", "from": "n1", "to": "n2"},
                            {"id": "e2", "from": "n2", "to": "n3"},
                        ],
                    },
                }
            ],
        },
    )

    assert result.status == "success"
    pipeline_result = result.cell_results["p1"]
    assert pipeline_result.output == [0]
    assert pipeline_result.node_outputs == {
        "n1": [],
        "n2": [],
        "n3": [0],
    }
