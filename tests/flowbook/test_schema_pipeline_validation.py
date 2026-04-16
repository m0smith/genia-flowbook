import pytest
from genia.flowbook.schema import validate_notebook, SchemaError

# --- Pipeline validation: duplicate node IDs ---
def test_pipeline_duplicate_node_ids():
    data = {
        "version": "1.0.0",
        "cells": [
            {
                "id": "p1",
                "type": "pipeline_cell",
                "pipeline": {
                    "nodes": [
                        {"id": "n1", "type": "source", "operation": "source"},
                        {"id": "n1", "type": "transform", "operation": "sum"}
                    ],
                    "edges": [
                        {"id": "e1", "from": "n1", "to": "n1"}
                    ]
                }
            }
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "Duplicate node ID" in str(exc.value)

# --- Pipeline validation: duplicate edge IDs ---
def test_pipeline_duplicate_edge_ids():
    data = {
        "version": "1.0.0",
        "cells": [
            {
                "id": "p1",
                "type": "pipeline_cell",
                "pipeline": {
                    "nodes": [
                        {"id": "n1", "type": "source", "operation": "source"},
                        {"id": "n2", "type": "transform", "operation": "sum"}
                    ],
                    "edges": [
                        {"id": "e1", "from": "n1", "to": "n2"},
                        {"id": "e1", "from": "n2", "to": "n1"}
                    ]
                }
            }
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "Duplicate edge ID" in str(exc.value)

# --- Pipeline validation: edge to non-existent node ---
def test_pipeline_edge_to_nonexistent_node():
    data = {
        "version": "1.0.0",
        "cells": [
            {
                "id": "p1",
                "type": "pipeline_cell",
                "pipeline": {
                    "nodes": [
                        {"id": "n1", "type": "source", "operation": "source"}
                    ],
                    "edges": [
                        {"id": "e1", "from": "n1", "to": "n2"}
                    ]
                }
            }
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "Edge references non-existent node" in str(exc.value)
