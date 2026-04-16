import pytest
from genia.flowbook.schema import validate_notebook, SchemaError

# --- Cycle detection: multi-cell ---
def test_cycle_detection_multicell():
    data = {
        "version": "1.0.0",
        "cells": [
            {"id": "v1", "type": "value_cell", "value": 1},
            {"id": "p1", "type": "pipeline_cell", "pipeline": {"nodes": [], "edges": []}, "depends_on": ["b1"]},
            {"id": "b1", "type": "binding_cell", "binding_name": "foo", "source_cell_id": "p1"}
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "Circular dependency" in str(exc.value) or "cycle" in str(exc.value)

# --- Cycle detection: multi-pipeline ---
def test_cycle_detection_multi_pipeline():
    data = {
        "version": "1.0.0",
        "cells": [
            {"id": "v1", "type": "value_cell", "value": 1},
            {"id": "p1", "type": "pipeline_cell", "pipeline": {"nodes": [], "edges": []}, "depends_on": ["p2"]},
            {"id": "p2", "type": "pipeline_cell", "pipeline": {"nodes": [], "edges": []}, "depends_on": ["p1"]}
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "Circular dependency" in str(exc.value) or "cycle" in str(exc.value)
