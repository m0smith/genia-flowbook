import pytest
from genia.flowbook.schema import validate_notebook, SchemaError

# --- Binding name conflicts: reserved operation name ---
def test_binding_name_conflict_with_reserved_op():
    data = {
        "version": "1.0.0",
        "cells": [
            {"id": "v1", "type": "value_cell", "value": 1},
            {"id": "b1", "type": "binding_cell", "binding_name": "sum", "source_cell_id": "v1"}
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "conflicts with reserved name" in str(exc.value)

# --- Binding name conflicts: duplicate binding name ---
def test_binding_name_conflict_duplicate():
    data = {
        "version": "1.0.0",
        "cells": [
            {"id": "v1", "type": "value_cell", "value": 1},
            {"id": "b1", "type": "binding_cell", "binding_name": "foo", "source_cell_id": "v1"},
            {"id": "b2", "type": "binding_cell", "binding_name": "foo", "source_cell_id": "v1"}
        ]
    }
    with pytest.raises(SchemaError) as exc:
        validate_notebook(data)
    assert "conflicts with reserved name" in str(exc.value) or "already exists" in str(exc.value)
