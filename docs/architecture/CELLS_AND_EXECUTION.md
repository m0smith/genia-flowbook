# Flowbook Architecture: Cells and Execution

**Status**: Specification (aligns with `docs/book/NOTEBOOK_SPEC.md`)

## Overview

Flowbook organizes computation into **notebooks** containing ordered **cells**. Each cell encapsulates a specific kind of task or data.

This document explains how cells relate to the existing FlowGraph prototype and the staged migration toward notebook execution.

Important:
- The current React app is a temporary host shell.
- The old TypeScript graph executor is not the product semantic authority.
- Browser-native Genia is not implemented yet.

---

## Cell Types and Their Roles

```
Notebook (ordered sequence of cells)
├── note_cell           [non-executable, informational]
├── value_cell          [executable, static data]
├── pipeline_cell       [executable, contains a FlowGraph]
├── inspect_cell        [executable, displays another cell's output]
└── binding_cell        [executable, binds a name to a cell's output]
```

### Data Flow Between Cells

```
value_cell → binding_cell → [other cells can reference the binding]
    ↑                             ↓
    └─────── depends_on ──────────┘

pipeline_cell → inspect_cell [displays output]
     ↑              ↓
     └── source_cell_id
```

---

## Relationship to FlowGraph

### Current (implemented)
- Single FlowGraph-shaped demo in the temporary React host shell
- Nodes: source / transform / sink
- Edges: connections between nodes
- Execution routed through a notebook-shaped compatibility boundary

### Notebook (specification)
- Multiple graphs, one per `pipeline_cell`
- Each `pipeline_cell` contains a FlowGraph
- Cells compose at a higher level, above individual operations

### Mapping
```
FlowGraph (existing)       → pipeline_cell.pipeline (specification)
Node                       → node in pipeline.nodes
Edge                       → edge in pipeline.edges
prototypeGraphToNotebook() → wrap graph as a single pipeline_cell notebook
executeNotebook()          → execute notebook-shaped data through the Flowbook boundary
```

---

## Execution Flow

### Phase 1: Parse and Validate
```
Raw JSON/data
    ↓
[Parse notebook structure]
    ↓
[Validate schema]
    ├─ Check cell IDs are unique
    ├─ Check all references exist
    ├─ Check no forward references (acyclicity)
    └─ Check all operations are resolvable
    ↓
Valid Notebook
```

### Phase 2: Execute Cells
```
For each cell in notebook order:
    ↓
[Execute cell based on type]
    │
    ├─→ note_cell        [no-op, skip]
    │
    ├─→ value_cell       [return {value}]
    │
    ├─→ pipeline_cell    [execute pipeline via Flowbook core / Genia direction]
    │                    └─ Current host path uses a temporary compatibility runtime
    │                    └─ Long-term ownership belongs in Genia
    │
    ├─→ inspect_cell     [get output of source_cell]
    │
    └─→ binding_cell     [execute source_cell, bind name]
    ↓
[Record output in execution context]
    ↓
[If error, stop (fail-fast) or mark cell as failed]
    ↓
Next cell (or halt)
```

---

## Execution Context

During notebook execution, maintain a context:

```
ExecutionContext {
  cellOutputs: Record<cell_id, output>,     // All cell outputs
  bindings: Record<binding_name, value>,    // Named bindings
  errors: Record<cell_id, error>,           // Per-cell errors
  halted: boolean,                          // Stop on first error?
}
```

---

## Error Handling

### Error types by phase:

**Parsing** (before execution)
- Malformed JSON/data
- Missing required fields

**Validation** (before execution)
- Duplicate cell IDs
- Forward references
- Unknown operations
- Missing references

**Execution** (during execution)
- Operation fails (e.g., division by zero)
- Cannot resolve operation
- Upstream cell failed
- Binding name conflicts

### Propagation

```
Cell executed successfully
    ↓
Output recorded in cellOutputs
    ↓
Dependent cells use this cell's output
    │
    └─→ If source cell failed:
            Dependent cell fails with "UPSTREAM_FAILURE"
```

---

## Determinism Guarantees

Same notebook, same input → same outputs, same order.

**What achieves this:**
1. Topological sort is deterministic (Kahn's algorithm)
2. Cell order is fixed (not random)
3. Operations are per-node pure functions
4. No shared mutable state between cells
5. No implicit retry/backoff logic

**What could break this (implementation must prevent):**
- Floating-point rounding differences (rare, but edge case)
- Non-deterministic operation registry
- Parallel execution (serialized in spec)
- External I/O side effects (operations should be pure)

---

## Composability via Pipelines

### Current model (single graph)
```
source → lines → map(parse_int) → sum
```

### Notebook model (per-cell pipelines)
```
Cell 1 (pipeline):  source → lines → [output: ["1","2","3","4","5"]]
Cell 2 (binding):   bind "numbers" to Cell1's output
Cell 3 (pipeline):  [reference: numbers] → map(parse_int) → sum
Cell 4 (inspect):   display Cell3's output
```

Each cell is independently composable via its pipeline.

---

## Implementation Considerations (Not part of spec)

These are hints for implementers; not defined in the spec:

1. **Cell execution engine**: Walk notebook in order, dispatch by cell type
2. **Dependency tracking**: Build backward-reference graph, verify acyclicity
3. **Operation registry**: Integrates with Genia interpreter's operations
4. **UI binding**: Host shell renders returned results; UI must not define semantics
5. **Error recovery**: Allow re-execution of cells after fixes (not in spec)
6. **Persistence**: Serialize notebooks to JSON files; deserialize and validate

---

## Non-Features (Out of Scope)

The spec explicitly does NOT cover:

- Real-time streaming execution
- Parallel cell execution
- Parameterized operations (future)
- Type annotations (future)
- Multi-user collaboration / locking
- Access control / authorization
- Caching / memoization
- Distributed execution
- Transactions / rollback
- Interactive re-execution within a cell

These can be added in future versions without changing the core spec.

---

**End of Architecture Document**
