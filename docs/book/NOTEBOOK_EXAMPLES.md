# Flowbook Specification: Worked Examples

This document shows example notebooks that conform to the Flowbook Notebook Core specification.

See `docs/book/NOTEBOOK_SPEC.md` for the formal specification.

---

## Example 1: Simple Pipeline Notebook

**Scenario**: Process numbers through a standard pipeline.

```json
{
  "version": "1.0.0",
  "metadata": {
    "author": "alice",
    "description": "Basic number processing"
  },
  "cells": [
    {
      "id": "intro",
      "type": "note_cell",
      "content": "# Number Processing\n\nThis notebook demonstrates a simple pipeline:\n1. Read source numbers\n2. Parse them as integers\n3. Sum the results"
    },
    {
      "id": "main-pipeline",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "n1", "type": "source", "operation": "source", "x": 100, "y": 200 },
          { "id": "n2", "type": "transform", "operation": "lines", "x": 300, "y": 200 },
          { "id": "n3", "type": "transform", "operation": "map(parse_int)", "x": 500, "y": 200 },
          { "id": "n4", "type": "sink", "operation": "sum", "x": 700, "y": 200 }
        ],
        "edges": [
          { "id": "n1->n2", "from": "n1", "to": "n2" },
          { "id": "n2->n3", "from": "n2", "to": "n3" },
          { "id": "n3->n4", "from": "n3", "to": "n4" }
        ]
      }
    },
    {
      "id": "result-display",
      "type": "inspect_cell",
      "source_cell_id": "main-pipeline",
      "format": "raw",
      "metadata": { "label": "Final Sum" }
    }
  ]
}
```

**Execution trace:**
1. Cell `intro`: Skipped (note_cell)
2. Cell `main-pipeline`: Executes, output = `[15]` (sum of 1..5)
3. Cell `result-display`: Displays output of `main-pipeline`

---

## Example 2: Multi-Pipeline Notebook with Bindings

**Scenario**: Analyze two datasets independently, then combine results.

```json
{
  "version": "1.0.0",
  "metadata": {
    "author": "bob",
    "description": "Multi-source analysis with binding"
  },
  "cells": [
    {
      "id": "doc",
      "type": "note_cell",
      "content": "# Dual Analysis\n\nWe compute statistics from two independent data sources."
    },
    {
      "id": "source-a",
      "type": "value_cell",
      "value": "10\n20\n30"
    },
    {
      "id": "source-b",
      "type": "value_cell",
      "value": "5\n15\n25"
    },
    {
      "id": "pipeline-a",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "na1", "type": "source", "operation": "source" },
          { "id": "na2", "type": "transform", "operation": "lines" },
          { "id": "na3", "type": "transform", "operation": "map(parse_int)" },
          { "id": "na4", "type": "sink", "operation": "sum" }
        ],
        "edges": [
          { "id": "na1->na2", "from": "na1", "to": "na2" },
          { "id": "na2->na3", "from": "na2", "to": "na3" },
          { "id": "na3->na4", "from": "na3", "to": "na4" }
        ]
      },
      "depends_on": ["source-a"]
    },
    {
      "id": "bind-sum-a",
      "type": "binding_cell",
      "binding_name": "sum_a",
      "source_cell_id": "pipeline-a"
    },
    {
      "id": "pipeline-b",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "nb1", "type": "source", "operation": "source" },
          { "id": "nb2", "type": "transform", "operation": "lines" },
          { "id": "nb3", "type": "transform", "operation": "map(parse_int)" },
          { "id": "nb4", "type": "sink", "operation": "sum" }
        ],
        "edges": [
          { "id": "nb1->nb2", "from": "nb1", "to": "nb2" },
          { "id": "nb2->nb3", "from": "nb2", "to": "nb3" },
          { "id": "nb3->nb4", "from": "nb3", "to": "nb4" }
        ]
      },
      "depends_on": ["source-b"]
    },
    {
      "id": "bind-sum-b",
      "type": "binding_cell",
      "binding_name": "sum_b",
      "source_cell_id": "pipeline-b"
    },
    {
      "id": "show-a",
      "type": "inspect_cell",
      "source_cell_id": "bind-sum-a",
      "format": "json"
    },
    {
      "id": "show-b",
      "type": "inspect_cell",
      "source_cell_id": "bind-sum-b",
      "format": "json"
    }
  ]
}
```

**Execution trace:**
1. `doc`: Skipped
2. `source-a`: Output = `["10\n20\n30"]`
3. `source-b`: Output = `["5\n15\n25"]`
4. `pipeline-a`: Output = `[60]`, depends on `source-a`
5. `bind-sum-a`: Binds `sum_a = [60]`
6. `pipeline-b`: Output = `[45]`, depends on `source-b`
7. `bind-sum-b`: Binds `sum_b = [45]`
8. `show-a`: Displays `[60]`
9. `show-b`: Displays `[45]`

Note: Steps 2–3 are independent and could execute in parallel (implementation choice).

---

## Example 3: Error Handling

**Scenario**: A notebook with an invalid operation triggers an error.

```json
{
  "version": "1.0.0",
  "cells": [
    {
      "id": "p1",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "n1", "type": "source", "operation": "source" },
          { "id": "n2", "type": "transform", "operation": "unknown_op" },
          { "id": "n3", "type": "sink", "operation": "sum" }
        ],
        "edges": [
          { "id": "n1->n2", "from": "n1", "to": "n2" },
          { "id": "n2->n3", "from": "n2", "to": "n3" }
        ]
      }
    },
    {
      "id": "p2",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "n4", "type": "source", "operation": "source" }
        ],
        "edges": []
      }
    }
  ]
}
```

**Execution result:**
```json
{
  "execution": {
    "p1": {
      "success": false,
      "error": {
        "type": "error",
        "code": "UNKNOWN_OPERATION",
        "message": "Operation 'unknown_op' is not registered",
        "cell_id": "p1",
        "location": {
          "step": "execution",
          "context": "Node 'n2' in pipeline_cell 'p1'"
        },
        "details": {
          "operation": "unknown_op",
          "node_id": "n2"
        }
      }
    },
    "p2": {
      "status": "not_executed",
      "reason": "UPSTREAM_FAILURE or halted by runner"
    }
  }
}
```

**Key points:**
- Cell `p1` fails with a structured error
- Cell `p2` is not executed (fail-fast behavior, or marked as skipped if runner continues)
- Error includes operation name, node ID, and cell context

---

## Example 4: Validation Errors

**Scenario**: A notebook with forward references (invalid acyclicity).

```json
{
  "version": "1.0.0",
  "cells": [
    {
      "id": "p1",
      "type": "pipeline_cell",
      "depends_on": ["v2"],
      "pipeline": {
        "nodes": [{ "id": "n1", "type": "source", "operation": "source" }],
        "edges": []
      }
    },
    {
      "id": "v2",
      "type": "value_cell",
      "value": 42
    }
  ]
}
```

**Validation error:**
```json
{
  "type": "error",
  "code": "FORWARD_REFERENCE",
  "message": "Cell 'p1' references cell 'v2' which appears after it",
  "location": {
    "step": "validation",
    "context": "Notebook structure validation"
  },
  "details": {
    "cell_id": "p1",
    "referenced_cell": "v2",
    "cell_position": 0,
    "referenced_position": 1
  }
}
```

**Key points:**
- Caught during validation, before execution
- Prevents cycles by enforcing backward references only

---

## Example 5: Schema Validation Error

**Scenario**: A binding_cell references a non-existent cell.

```json
{
  "version": "1.0.0",
  "cells": [
    {
      "id": "b1",
      "type": "binding_cell",
      "binding_name": "my_value",
      "source_cell_id": "nonexistent"
    }
  ]
}
```

**Validation error:**
```json
{
  "type": "error",
  "code": "MISSING_CELL_REFERENCE",
  "message": "Cell 'b1' references cell 'nonexistent' which does not exist",
  "location": {
    "step": "validation",
    "context": "binding_cell 'b1' field 'source_cell_id'"
  },
  "details": {
    "cell_id": "b1",
    "field": "source_cell_id",
    "referenced_id": "nonexistent",
    "available_cells": []
  }
}
```

---

## Example 6: Complex Pipeline with Multiple Sinks

**Scenario**: A pipeline with branching logic (advanced; shows limits of current spec).

```json
{
  "version": "1.0.0",
  "cells": [
    {
      "id": "branching",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "n1", "type": "source", "operation": "source" },
          { "id": "n2", "type": "transform", "operation": "lines" },
          { "id": "n3", "type": "transform", "operation": "map(parse_int)" },
          { "id": "n4", "type": "sink", "operation": "sum" },
          { "id": "n5", "type": "sink", "operation": "count" }
        ],
        "edges": [
          { "id": "n1->n2", "from": "n1", "to": "n2" },
          { "id": "n2->n3", "from": "n2", "to": "n3" },
          { "id": "n3->n4", "from": "n3", "to": "n4" },
          { "id": "n3->n5", "from": "n3", "to": "n5" }
        ]
      }
    }
  ]
}
```

**Execution result:**
The pipeline has two sinks. Behavior depends on implementation:
- Output is the last sink's output (deterministic, by topological order)
- Or: outputs from all sinks (future enhancement)

**Note**: The spec currently returns "final node output" (singular). Multiple sinks are allowed but not fully specified. This is intentionally left for future clarification when the Genia interpreter provides clearer semantics.

---

## Conformance Checklist

Any notebook is valid if it:

- [ ] Is parseable as JSON
- [ ] Has unique `version` field
- [ ] All cells have unique `id` and valid `type`
- [ ] Each cell's schema matches its type
- [ ] All `source_cell_id` references point to earlier cells
- [ ] All `depends_on` references point to earlier cells
- [ ] All referenced cells exist
- [ ] All operation names are resolvable
- [ ] No circular dependencies
- [ ] All binding names are unique
- [ ] All edge endpoints reference existing nodes (within their pipeline)
- [ ] No pipelines contain cycles (DAG constraint)

---

**End of Worked Examples**
