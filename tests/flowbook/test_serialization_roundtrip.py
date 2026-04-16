import pytest
from genia.flowbook.schema import validate_notebook
from genia.flowbook.serialize import notebook_to_dict
from genia.flowbook.model import Notebook

# --- Round-trip: all cell types, all optional fields ---
def test_round_trip_all_cell_types():
    data = {
        "version": "1.0.0",
        "metadata": {"author": "A", "description": "desc"},
        "cells": [
            {"id": "n1", "type": "note_cell", "content": "hello", "metadata": {"label": "lbl"}},
            {"id": "v1", "type": "value_cell", "value": 42},
            {"id": "p1", "type": "pipeline_cell", "pipeline": {"nodes": [], "edges": []}, "depends_on": []},
            {"id": "i1", "type": "inspect_cell", "source_cell_id": "v1", "format": "json"},
            {"id": "b1", "type": "binding_cell", "binding_name": "foo", "source_cell_id": "v1"}
        ]
    }
    nb: Notebook = validate_notebook(data)
    dumped = notebook_to_dict(nb)
    nb2: Notebook = validate_notebook(dumped)
    dumped2 = notebook_to_dict(nb2)
    assert dumped == dumped2

# --- Round-trip: missing optional fields ---
def test_round_trip_missing_optional_fields():
    data = {
        "cells": [
            {"id": "v1", "type": "value_cell", "value": 1}
        ]
    }
    nb = validate_notebook(data)
    dumped = notebook_to_dict(nb)
    nb2 = validate_notebook(dumped)
    dumped2 = notebook_to_dict(nb2)
    assert dumped == dumped2
