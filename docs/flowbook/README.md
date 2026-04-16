# Flowbook Notebook Core (Clarified)

Flowbook is a data-centric, flow-based notebook system for the Genia language. It models programs as explicit, composable graphs of cells and pipelines, not as text code.

## Key Concepts

- **Notebook:** Ordered list of cells, each with a unique ID.
- **Cell:** Five types:
  - `note_cell`: Markdown/text, non-executable.
  - `value_cell`: Holds a literal value.
  - `pipeline_cell`: Runs a pipeline DAG.
  - `inspect_cell`: Displays output from another cell.
  - `binding_cell`: Binds a name to another cell's output (binds the *entire array output*).
- **Pipeline:** DAG of operations, defined in a `pipeline_cell`.
  - Node fields `x`, `y` are optional and ignored by execution.
- **References:** Cells can reference outputs of earlier cells (never forward).
- **Execution:** Cells execute in dependency order, with results cached per run.

## Example Notebook

```json
{
  "version": "1.0.0", // optional
  "cells": [
    {"id": "v1", "type": "value_cell", "value": [1, 2, 3, 4, 5]},
    {"id": "p1", "type": "pipeline_cell", "pipeline": {
      "nodes": [
        {"id": "n1", "type": "source", "operation": "source"},
        {"id": "n2", "type": "transform", "operation": "sum"}
      ],
      "edges": [
        {"id": "e1", "from": "n1", "to": "n2"}
      ]
    }, "depends_on": ["v1"]}
  ]
}
```

*Fields marked as optional may be omitted if not needed.*
