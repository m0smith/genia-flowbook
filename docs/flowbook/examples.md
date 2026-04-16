# Flowbook Examples (Clarified)

## 1. Minimal Notebook

```json
{
  "version": "1.0.0", // optional
  "cells": [
    {
      "id": "v1",
      "type": "value_cell",
      "value": [1, 2, 3]
    },
    {
      "id": "p1",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          {"id": "n1", "type": "source", "operation": "source"},
          {"id": "n2", "type": "transform", "operation": "sum"}
        ],
        "edges": [
          {"id": "e1", "from": "n1", "to": "n2"}
        ]
      },
      "depends_on": ["v1"] // optional, but recommended for clarity
    }
  ]
}
```

*Fields marked as optional may be omitted if not needed.*

## 2. Pipeline Example

```json
{
  "cells": [
    {"id": "v1", "type": "value_cell", "value": [1, 2, 3, 4, 5]},
    {"id": "p1", "type": "pipeline_cell", "pipeline": {
      "nodes": [
        {"id": "n1", "type": "source", "operation": "source"},
        {"id": "n2", "type": "transform", "operation": "filter(x => x % 2 == 0)"},
        {"id": "n3", "type": "transform", "operation": "sum"}
      ],
      "edges": [
        {"id": "e1", "from": "n1", "to": "n2"},
        {"id": "e2", "from": "n2", "to": "n3"}
      ]
    }, "depends_on": ["v1"]}
  ]
}
```

*Pipeline node fields `x` and `y` are optional and ignored by execution.*

## 3. Reference Example

```json
{
  "cells": [
    {"id": "v1", "type": "value_cell", "value": [10, 20, 30]},
    {"id": "p1", "type": "pipeline_cell", "pipeline": {
      "nodes": [
        {"id": "n1", "type": "source", "operation": "source"},
        {"id": "n2", "type": "transform", "operation": "sum"}
      ],
      "edges": [
        {"id": "e1", "from": "n1", "to": "n2"}
      ]
    }, "depends_on": ["v1"]},
    {"id": "b1", "type": "binding_cell", "binding_name": "total", "source_cell_id": "p1"}
  ]
}
```

> The binding cell binds the *entire array output* of the referenced cell.

## 4. Error Example

```json
{
  "cells": [
    {"id": "v1", "type": "value_cell", "value": [1, 2, 3]},
    {"id": "p1", "type": "pipeline_cell", "pipeline": {
      "nodes": [
        {"id": "n1", "type": "source", "operation": "source"},
        {"id": "n2", "type": "transform", "operation": "unknown_op"}
      ],
      "edges": [
        {"id": "e1", "from": "n1", "to": "n2"}
      ]
    }, "depends_on": ["v1"]}
  ]
}
```

*All examples are valid and runnable if required fields are present. Optional fields may be omitted.*
