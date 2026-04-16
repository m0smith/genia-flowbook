import pytest
from genia.flowbook.schema import validate_notebook, SchemaError
from genia.flowbook.errors import StructuredError

# --- Error structure: all required fields ---
def test_error_structure_all_fields():
    data = {
        "cells": [
            {"id": "v1", "type": "value_cell"}  # missing value
        ]
    }
    try:
        validate_notebook(data)
    except SchemaError as e:
        err: StructuredError = e.structured_error
        assert err.type == "error"
        assert err.code
        assert err.message
        assert err.location
        assert hasattr(err.location, "step")
        assert hasattr(err.location, "context")
        # cell_id may be None for parse errors, but present for cell errors
        # details and timestamp are optional
    else:
        assert False, "SchemaError not raised"
