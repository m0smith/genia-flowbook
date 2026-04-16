# Flowbook Notebook Specification

**Version:** 0.1  
**Status:** Specification (not implementation)  
**Authority:** `PROJECT_STATE.md` is final truth  

---

## 1. Notebook Structure

A notebook is a container for cells organized as an ordered sequence.

### 1.1 Required fields
- `version` (string): Semantic version of the notebook format (e.g., "1.0.0")
- `cells` (array of Cell): Ordered cell sequence; execution follows this order
- `metadata` (object, optional): Notebook-level metadata (e.g., author, created_at)

### 1.2 Optional fields
- `metadata.author` (string, optional): Creator name or identifier
- `metadata.description` (string, optional): Purpose or summary
- `metadata.created_at` (ISO-8601 string, optional): Creation timestamp
- `metadata.source` (string, optional): Origin or reference

### 1.3 Validation rules
- A notebook MUST have at least one cell
- All cell IDs within a notebook MUST be unique
- Cells MUST be ordered by execution dependency
  - A cell cannot reference (via `depends_on`) a cell that appears after it
  - This enforces that dependencies always point backward
- MUST be valid Genia data (parseable as JSON or native Genia value)

### 1.4 Example notebook structure
```json
{
  "version": "1.0.0",
  "metadata": {
    "author": "alice",
    "description": "Word frequency analyzer",
    "created_at": "2026-04-16T10:30:00Z"
  },
  "cells": [
    { "id": "c1", "type": "note_cell", ... },
    { "id": "c2", "type": "value_cell", ... },
    { "id": "c3", "type": "pipeline_cell", ... }
  ]
}
```

---

## 2. Cell Model

All cells share a common base structure; type-specific fields extend it.

### 2.1 Cell base (required for all cells)
- `id` (string): Unique identifier within the notebook
- `type` (enum): One of: `note_cell`, `value_cell`, `pipeline_cell`, `inspect_cell`, `binding_cell`
- `metadata` (object, optional): Cell-level metadata

### 2.2 Cell types and schemas

#### 2.2.1 note_cell
A markdown/text cell for documentation or annotations. Not executable.

**Schema:**
- `id` (string): Unique cell identifier
- `type` (enum): `"note_cell"`
- `content` (string): Markdown text
- `metadata` (object, optional): Cell metadata

**Validation:**
- `content` MUST be non-empty string

**Execution:**
- No execution; purely informational

**Example:**
```json
{
  "id": "note-1",
  "type": "note_cell",
  "content": "## Analysis\n\nThis section cleans the raw data."
}
```

---

#### 2.2.2 value_cell
Holds a literal value or constant. Produces output but has no input dependencies.

**Schema:**
- `id` (string): Unique cell identifier
- `type` (enum): `"value_cell"`
- `value` (any): A Genia value (string, number, array, object, null, boolean)
- `metadata` (object, optional): Cell metadata

**Validation:**
- `value` MUST be a valid Genia value
- `value` MUST NOT be undefined or NaN

**Execution:**
- Output: `[value]` (wrapped in an array as per Genia pipeline convention)
- No dependencies

**Example:**
```json
{
  "id": "v1",
  "type": "value_cell",
  "value": "hello"
}
```

Output: `["hello"]`

---

#### 2.2.3 pipeline_cell
Contains a directed acyclic graph (DAG) of operations. The core execution unit.

**Schema:**
- `id` (string): Unique cell identifier
- `type` (enum): `"pipeline_cell"`
- `pipeline` (object):
  - `nodes` (array of PipelineNode): Operations in the graph
  - `edges` (array of PipelineEdge): Connections between nodes
- `depends_on` (array of cell IDs, optional): External cell IDs this pipeline depends on
- `metadata` (object, optional): Cell metadata

**PipelineNode schema:**
- `id` (string): Node ID within this pipeline (unique within the pipeline)
- `type` (enum): `"source"`, `"transform"`, `"sink"`
- `operation` (string): Operation name (resolved from available operations registry)
- `x` (number, optional): UI x-coordinate (ignored by execution)
- `y` (number, optional): UI y-coordinate (ignored by execution)

**PipelineEdge schema:**
- `id` (string): Edge ID (typically `"from_id->to_id"`)
- `from` (string): Source node ID
- `to` (string): Destination node ID

**Validation:**
- Pipeline MUST be a DAG (no cycles allowed)
- All nodes referenced in edges MUST exist in `nodes`
- All operations MUST be resolvable (e.g., registered in the Genia interpreter)
- If `depends_on` is present:
  - All referenced cell IDs MUST exist in the notebook
  - No circular inter-cell dependencies allowed
  - Referenced cells MUST appear before this cell in the notebook

**Execution:**
- Nodes are executed in topological order within the pipeline
- Inputs to a node come from flattened outputs of parent nodes
- Output: Result of the final (sink) node(s), or error

**Example:**
```json
{
  "id": "p1",
  "type": "pipeline_cell",
  "pipeline": {
    "nodes": [
      { "id": "n1", "type": "source", "operation": "source", "x": 100, "y": 200 },
      { "id": "n2", "type": "transform", "operation": "lines", "x": 300, "y": 200 },
      { "id": "n3", "type": "sink", "operation": "sum", "x": 500, "y": 200 }
    ],
    "edges": [
      { "id": "n1->n2", "from": "n1", "to": "n2" },
      { "id": "n2->n3", "from": "n2", "to": "n3" }
    ]
  }
}
```

---

#### 2.2.4 inspect_cell
Displays the output of a referenced cell. Non-transforming display only.

**Schema:**
- `id` (string): Unique cell identifier
- `type` (enum): `"inspect_cell"`
- `source_cell_id` (string): ID of the cell whose output to inspect
- `format` (string, optional): Display format hint (e.g., `"json"`, `"table"`, `"raw"`)
- `metadata` (object, optional): Cell metadata

**Validation:**
- `source_cell_id` MUST reference an existing cell in the notebook
- `source_cell_id` MUST appear before this cell in the notebook
- Referenced cell MUST be executable (not a `note_cell`)

**Execution:**
- No independent execution; renders/displays the output of `source_cell_id`
- Output: Same as the referenced cell's output
- If referenced cell has not been executed or has an error, output is an error

**Example:**
```json
{
  "id": "i1",
  "type": "inspect_cell",
  "source_cell_id": "p1",
  "format": "json"
}
```

---

#### 2.2.5 binding_cell
Binds a name to a value for use in other cells. Enables reference by name in expressions.

**Schema:**
- `id` (string): Unique cell identifier
- `type` (enum): `"binding_cell"`
- `binding_name` (string): Name to bind (alphanumeric + `_`, must not conflict with reserved names)
- `source_cell_id` (string): ID of the cell whose output to bind
- `metadata` (object, optional): Cell metadata

**Validation:**
- `binding_name` MUST be a valid identifier (Genia naming rules)
- `binding_name` MUST NOT conflict with built-in operation names or reserved keywords
- All binding names in a notebook MUST be unique
- `source_cell_id` MUST reference an existing cell in the notebook
- `source_cell_id` MUST appear before this cell in the notebook
- Referenced cell MUST be executable (not a `note_cell`)

**Execution:**
- Binds the output of `source_cell_id` to `binding_name` in the notebook's execution context
- Output: Same as the referenced cell's output, plus the binding side-effect
- If referenced cell has not been executed or has an error, binding fails with an error

**Registry:**
- After execution, `binding_name` is available as a reference in cells appearing after this binding

**Example:**
```json
{
  "id": "b1",
  "type": "binding_cell",
  "binding_name": "word_count",
  "source_cell_id": "p1"
}
```

After this binding, other cells can reference `word_count` (e.g., in a parameter or source operation).

---

## 3. Pipeline Model

A pipeline is the computation substrate, defined within a `pipeline_cell`.

### 3.1 Source types
Each node in a pipeline has a type that defines its role:

- **source**: Entry point; produces initial data
  - May reference an external input or literal
  - Takes no data input (in-degree = 0)
  - One or more sources allowed per pipeline

- **transform**: Intermediate operation
  - Takes input from parent nodes
  - Produces output for child nodes

- **sink**: Terminal operation
  - Takes input from parent nodes
  - Final output of the pipeline
  - May be multiple sinks, but execution returns final node's output

### 3.2 Step structure
Each node is an operation application:

- `operation` (string): Name of the operation (e.g., `"lines"`, `"sum"`, `"map(parse_int)"`)
- `args` (optional, implicit): Arguments are encoded in the operation string or provided by execution context
  - For now, operations are resolved by name from the registry
  - Parameterized operations may be supported in future versions

### 3.3 Data flow
- Data flows as **lists** (Genia arrays)
- Each node receives the flattened outputs of all parent nodes
- Node output is a list that becomes input to all child nodes
- No implicit type coercion; explicit transformation via operations

### 3.4 Execution contract
- Nodes execute once in topological order
- No backtracking or re-execution within a pipeline
- If any node fails, the entire pipeline fails (see Section 6)

---

## 4. Reference System

Cells can reference other cells by ID or by binding name.

### 4.1 Cell ID vs binding name
- **Cell ID**: Direct reference to a cell (e.g., `"c1"`)
  - Used in `depends_on`, `source_cell_id` fields
  - Immutable and scoped to the notebook
  - Always points to one cell

- **Binding name**: Semantic alias for a value
  - Introduced by `binding_cell`
  - May be used in operation parameters or expressions
  - Scoped to the notebook; must be unique

### 4.2 Reference rules
- A cell may reference another cell only if the referenced cell appears earlier in the notebook
  - Forward references are forbidden
  - This ensures acyclic dependencies

- `inspect_cell` and `binding_cell` must explicitly name the source cell via `source_cell_id`

- `pipeline_cell` may reference external bindings in the `depends_on` field and in operation parameters
  - Not all operations support parameter binding yet (see `PROJECT_STATE.md`)

### 4.3 Failure handling
- If a referenced cell's execution fails, dependent cells fail (cascading error)
- An attempt to reference a non-existent cell is a validation error (caught during parsing)
- Circular references are a validation error (caught during parsing via forward-reference check)

---

## 5. Execution Model

The notebook execution model is deterministic and order-preserving.

### 5.1 Order of execution
1. **Parse and validate** the notebook structure
   - Check all cell IDs are unique
   - Check all references are backward (no forward references)
   - Check all operations are resolvable
2. **Execute cells in notebook order**, top to bottom
   - `note_cell`: Skipped (not executable)
   - `value_cell`: Executed (returns the value)
   - `pipeline_cell`: Executed (runs the DAG)
   - `inspect_cell`: Executed (returns the source cell's output)
   - `binding_cell`: Executed (binds the source cell's output and returns it)

### 5.2 Re-execution rules
- A cell is not re-executed unless explicitly requested
- If a cell depends on a cell that was modified, the dependent cell must be re-executed
  - This is typically handled by the notebook UI/runner, not the core engine

### 5.3 Error isolation
- If a cell execution fails:
  - The error is recorded in the cell's execution result
  - Dependent cells downstream are marked as **not executed** (due to upstream failure)
  - Execution may continue for independent cells (DAG allows this) or halt globally (implementation choice)
  - Default behavior: **halt globally** (fail-fast)

### 5.4 Determinism guarantees
- Same notebook input → same outputs (assuming operations are deterministic)
- Execution order is always cell order, never random or parallel
- No shared mutable state between cell executions
- Each pipeline's topological order is deterministic (same input → same order)

---

## 6. Error Model

Errors are structured and explicit. No silent failures.

### 6.1 Structured error format
All errors follow a common schema:

```json
{
  "type": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable message",
  "cell_id": "c1",
  "location": {
    "step": "parsing" | "validation" | "execution",
    "context": "description of where in the process"
  },
  "details": {}
}
```

- `type` (string): Always `"error"`
- `code` (string): Machine-readable error code
- `message` (string): Human-readable description
- `cell_id` (string): ID of the cell where the error occurred (optional for parsing errors)
- `location` (object):
  - `step` (enum): `"parsing"`, `"validation"`, or `"execution"`
  - `context` (string): More specific location info
- `details` (object): Additional context (depends on error code)

### 6.2 Error codes (non-exhaustive)
- `PARSE_ERROR`: Notebook structure is invalid JSON/syntax
- `INVALID_SCHEMA`: Cell or notebook structure does not match schema
- `DUPLICATE_CELL_ID`: Two cells have the same ID
- `UNKNOWN_OPERATION`: Operation name is not registered
- `CYCLE_DETECTED`: Circular dependency between cells
- `FORWARD_REFERENCE`: Cell references a later cell (invalid)
- `MISSING_CELL_REFERENCE`: Referenced cell does not exist
- `EXECUTION_FAILED`: Runtime error in operation
- `UPSTREAM_FAILURE`: Cell not executed due to dependency failure

### 6.3 Cell-level vs step-level errors
- **Cell-level error**: The cell as a whole failed (e.g., unknown operation)
  - Reported in the cell's execution result
  - Affects dependent cells

- **Step-level error**: A node within a pipeline failed
  - Includes the node ID and operation name
  - Reported in the pipeline execution result along with all node outputs up to the point of failure

### 6.4 Example error
```json
{
  "type": "error",
  "code": "UNKNOWN_OPERATION",
  "message": "Operation 'nonexistent' is not registered",
  "cell_id": "p1",
  "location": {
    "step": "execution",
    "context": "Node 'n1' in pipeline_cell 'p1'"
  },
  "details": {
    "operation": "nonexistent",
    "node_id": "n1",
    "available_operations": ["source", "lines", "sum"]
  }
}
```

---

## 7. Serialization Format

Notebooks are serialized as valid Genia data (JSON-compatible).

### 7.1 Serialization rules
- Notebooks MUST be serializable to JSON
- All cell fields MUST be JSON-compatible (no undefined, no circular references, no functions)
- Metadata may be empty objects or omitted entirely
- The file format is JSON (`.json` or `.flowbook` extension)

### 7.2 Round-trip guarantee
- A notebook that is parsed → executed → serialized SHOULD produce the same structure
  - Execution results (outputs) are NOT serialized; only the notebook structure
  - Metadata is preserved
  - Cell order is preserved

### 7.3 Example serialized notebook
```json
{
  "version": "1.0.0",
  "metadata": {
    "author": "alice",
    "created_at": "2026-04-16T10:30:00Z"
  },
  "cells": [
    {
      "id": "c1",
      "type": "note_cell",
      "content": "# Data Pipeline\n\nThis notebook processes raw data."
    },
    {
      "id": "v1",
      "type": "value_cell",
      "value": [1, 2, 3, 4, 5]
    },
    {
      "id": "p1",
      "type": "pipeline_cell",
      "pipeline": {
        "nodes": [
          { "id": "n1", "type": "source", "operation": "source" },
          { "id": "n2", "type": "transform", "operation": "lines" },
          { "id": "n3", "type": "sink", "operation": "sum" }
        ],
        "edges": [
          { "id": "n1->n2", "from": "n1", "to": "n2" },
          { "id": "n2->n3", "from": "n2", "to": "n3" }
        ]
      }
    }
  ]
}
```

---

## 8. Summary: Core Invariants

These invariants MUST ALWAYS hold:

1. **Acyclicity**: No circular dependencies between cells or within pipelines
2. **Backward references only**: A cell cannot reference cells that appear after it
3. **Unique identifiers**: All cell IDs within a notebook are unique
4. **Explicit data flow**: All data flow is explicit; no implicit coercion or defaults
5. **Deterministic execution**: Same input always produces same output in same order
6. **Error isolation**: Errors in one cell do not corrupt independent cells
7. **Composability**: Cells compose via pipelines; no non-composable control structures
8. **No mutation**: Execution does not mutate the notebook structure
9. **Valid Genia data**: The entire notebook is valid Genia data

---

## 9. What This Spec Is NOT

- **Not implementation code**: This spec defines structure and contracts, not algorithms
- **Not UI design**: UI rendering, layout, and interaction are separate concerns
- **Not operation semantics**: Individual operations (e.g., `sum`, `lines`) are defined elsewhere in the Genia interpreter
- **Not speculation**: Only documents behavior that follows from existing Genia principles
- **Not authorization/security**: Access control and multi-user semantics are out of scope
- **Not real-time**: Execution is sequential and offline; no streaming or live updates are specified here

---

## 10. Future Extensions (Not in this spec)

These are possible future directions but are NOT part of this specification:

- Parameterized operations (e.g., `map(fn)` where `fn` is a parameter)
- Streaming/incremental execution
- Parallel pipeline execution
- Named parameters for operations
- Type annotations
- Conditional branching at the cell level
- Loop constructs
- Transaction/rollback semantics
- Distributed execution

---

**End of Specification**
