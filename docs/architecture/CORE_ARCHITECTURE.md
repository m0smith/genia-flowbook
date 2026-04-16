# Flowbook Notebook Core: Internal Architecture Design

**Status**: Design only (not implementation)  
**Target**: Portable implementation for JS, Python, future hosts  
**Authority**: Aligns with `docs/book/NOTEBOOK_SPEC.md`

---

## 1. Design Summary

### Vision
The Flowbook Notebook Core is a **pure data + execution engine** that implements the notebook specification. It:
- Owns the notebook structure, validation, and execution model
- Delegates operation execution to the Genia interpreter
- Provides a portable API that any host (JS, Python) can implement
- Remains agnostic to UI concerns (rendering, layout, interaction)

### Core Principles
1. **Explicit over implicit**: All state is visible and trackable
2. **Thin wrapper**: Notebook is a container; pipelines are delegated to Genia
3. **Deterministic**: Same input → same execution path, same output
4. **Portable**: No host-specific code in core; integration layer is separate
5. **Immutable model**: The spec structure is immutable; execution results are separate

### Design Scope
- **Core responsibility**: Parse → Validate → Execute → Report
- **Genia responsibility**: Resolve operations, execute pipeline DAGs
- **UI responsibility**: Render, select, interact (not in this design)
- **Future work**: Streaming, partial recomputation, caching strategies

---

## 2. Core Structures

All structures are defined logically; implementations may vary by host.

### 2.1 Notebook (immutable spec structure)

```
Notebook
├─ version: string                    [e.g., "1.0.0"]
├─ metadata: NotebookMetadata         [optional]
│  ├─ author?: string
│  ├─ description?: string
│  ├─ created_at?: ISO8601String
│  └─ source?: string
└─ cells: Cell[]                      [ordered; length >= 1]
```

**Invariants:**
- `cells` is non-empty
- All cell IDs are unique
- Cells are ordered such that dependencies always point backward

**Purpose**: Immutable source structure from serialized data. Never mutated during execution.

---

### 2.2 Cell (discriminated union by type)

**Base (all cells share):**
```
CellBase
├─ id: string                         [unique within notebook]
├─ type: CellType                     [discriminant]
└─ metadata?: CellMetadata            [optional]
```

**CellType variants:**

#### NoteCellSpec
```
NoteCellSpec extends CellBase
├─ type: "note_cell"
├─ content: string                    [non-empty markdown]
└─ metadata?: CellMetadata
```
- Never executed
- No dependencies
- No output

#### ValueCellSpec
```
ValueCellSpec extends CellBase
├─ type: "value_cell"
├─ value: GeniaValue                  [string | number | boolean | array | object | null]
└─ metadata?: CellMetadata
```
- Trivial execution (return value)
- No dependencies
- Output: [value] (wrapped in array)

#### PipelineCellSpec
```
PipelineCellSpec extends CellBase
├─ type: "pipeline_cell"
├─ pipeline: Pipeline
│  ├─ nodes: PipelineNode[]          [unique IDs within pipeline]
│  └─ edges: PipelineEdge[]
├─ depends_on?: string[]              [cell IDs; must be earlier cells]
└─ metadata?: CellMetadata
```
- Execution: delegate to Genia interpreter (topological order)
- Output: result of final node
- Dependencies: explicitly listed in depends_on

#### InspectCellSpec
```
InspectCellSpec extends CellBase
├─ type: "inspect_cell"
├─ source_cell_id: string             [must be earlier cell]
├─ format?: string                    [hint only; e.g., "json", "table", "raw"]
└─ metadata?: CellMetadata
```
- Execution: fetch and return output of source cell
- No independent computation
- Output: same as source cell

#### BindingCellSpec
```
BindingCellSpec extends CellBase
├─ type: "binding_cell"
├─ binding_name: string               [identifier, must be unique in notebook]
├─ source_cell_id: string             [must be earlier cell]
└─ metadata?: CellMetadata
```
- Execution: fetch source cell output, bind name
- Output: same as source cell (plus binding side-effect)
- Binding registered in execution context for later reference

---

### 2.3 Pipeline (core Genia container)

```
Pipeline
├─ nodes: PipelineNode[]
└─ edges: PipelineEdge[]
```

**PipelineNode:**
```
PipelineNode
├─ id: string                         [unique within this pipeline]
├─ type: "source" | "transform" | "sink"
├─ operation: string                  [name; e.g., "source", "lines", "sum"]
├─ x?: number                         [UI coordinate, ignored by execution]
└─ y?: number                         [UI coordinate, ignored by execution]
```

**PipelineEdge:**
```
PipelineEdge
├─ id: string                         [typically "from->to"]
├─ from: string                       [node ID]
└─ to: string                         [node ID]
```

**Invariants:**
- Must be a DAG (no cycles)
- All edges point to existing nodes
- All operations must be resolvable

**Purpose**: Container for Genia operation graph. Semantics delegated to Genia interpreter.

---

### 2.4 Execution Context (mutable state during execution)

```
ExecutionContext
├─ notebook: Notebook                 [immutable spec]
├─ cellResults: Map<cell_id, CellResult>     [populated during execution]
├─ bindings: Map<binding_name, GeniaValue>   [populated by binding_cells]
├─ errors: Map<cell_id, StructuredError>    [populated if cells fail]
└─ executionOrder: string[]                  [topologically sorted cell IDs]
```

**CellResult (union type by status):**

**CellResult.Success:**
```
CellResultSuccess
├─ status: "success"
├─ cellId: string
├─ cellType: CellType
├─ output: GeniaValue[]              [always an array]
└─ executedAt?: timestamp
```

**CellResult.Skipped:**
```
CellResultSkipped
├─ status: "skipped"
├─ cellId: string
├─ reason: "note_cell" | "upstream_failure" | "halted" | string
```

**CellResult.Error:**
```
CellResultError
├─ status: "error"
├─ cellId: string
├─ error: StructuredError
└─ executedAt?: timestamp
```

**Purpose**: Mutable store of execution state. Used during and after notebook execution. Not serialized.

---

### 2.5 Dependency Graph (computed analysis structure)

```
DependencyGraph
├─ nodeById: Map<cell_id, DependencyNode>
├─ edges: Set<(from_id, to_id)>
└─ topologicalOrder: string[]        [or error if cycle detected]
```

**DependencyNode:**
```
DependencyNode
├─ cellId: string
├─ cellType: CellType
├─ directDependencies: Set<cell_id>  [cells this depends on]
├─ transitiveDependencies: Set<cell_id> [computed closure]
└─ status: "valid" | "cycle" | "forward_ref" | ...
```

**Purpose**: Computed during validation. Supports:
- Acyclicity checking
- Execution ordering
- Dependency tracking for selective recomputation (future)

---

### 2.6 Structured Error

```
StructuredError
├─ type: "error"                      [literal]
├─ code: ErrorCode                    [e.g., "UNKNOWN_OPERATION"]
├─ message: string                    [human-readable]
├─ location: ErrorLocation
│  ├─ step: "parsing" | "validation" | "execution"
│  └─ context: string                 [e.g., "Node 'n2' in pipeline_cell 'p1'"]
├─ cellId?: string                    [optional for parse errors]
├─ details: Record<string, any>       [error-specific context]
└─ timestamp?: ISO8601String
```

**ErrorCode (non-exhaustive):**
```
"PARSE_ERROR"
"INVALID_SCHEMA"
"DUPLICATE_CELL_ID"
"UNKNOWN_OPERATION"
"CYCLE_DETECTED"
"FORWARD_REFERENCE"
"MISSING_CELL_REFERENCE"
"EXECUTION_FAILED"
"UPSTREAM_FAILURE"
```

**Purpose**: Machine-readable and UI-displayable error information.

**Invariant**: One error per cell (first error found is recorded; execution halts).

---

### 2.7 Reference

```
Reference
├─ type: "cell_id" | "binding_name"
├─ target: string
└─ resolved?: GeniaValue              [populated after resolution]
```

**Resolved reference:**
```
ResolvedReference
├─ target: string
├─ value: GeniaValue[]                [output from referenced cell]
└─ status: "success" | "error"
```

**Purpose**: Tracks how cells refer to other cells. Enables validation and runtime resolution.

---

## 3. Module Layout

### Proposed package structure (host-agnostic)

```
flowbook-core/
├─ spec/
│  └─ types.ts|py                     # TypeScript type definitions or Python dataclasses
│     [Notebook, Cell, Pipeline, etc. — match NOTEBOOK_SPEC.md exactly]
│
├─ schema/
│  ├─ parser.ts|py                    # JSON → Notebook (parsing)
│  └─ validator.ts|py                 # Notebook → ValidationResult
│
├─ model/
│  ├─ notebook.ts|py                  # NotebookModel (runtime wrapper)
│  ├─ dependency.ts|py                # DependencyGraph analysis
│  └─ reference.ts|py                 # Reference resolution
│
├─ engine/
│  ├─ executor.ts|py                  # ExecutionEngine (full notebook)
│  ├─ cell-executor.ts|py             # Single-cell execution logic
│  └─ context.ts|py                   # ExecutionContext
│
├─ errors/
│  ├─ structured-error.ts|py          # StructuredError construction
│  └─ codes.ts|py                     # Error code constants
│
├─ serialization/
│  ├─ to-genia.ts|py                  # Notebook → Genia data
│  ├─ from-genia.ts|py                # Genia data → Notebook
│  └─ normalizer.ts|py                # Normalization
│
├─ interop/
│  ├─ genia-stdlib.ts|py              # Interface to Genia interpreter
│  └─ operation-registry.ts|py        # Operation name resolution
│
└─ public/
   └─ api.ts|py                       # Public entry points
      ├─ loadNotebook(data: GeniaValue)
      ├─ executeNotebook(nb: Notebook)
      ├─ executeSingleCell(nb, cellId)
      └─ validateNotebook(nb: Notebook)
```

### Module responsibilities

| Module | Responsibility | Depends On |
|--------|---|---|
| **spec** | Type definitions matching NOTEBOOK_SPEC.md | nothing |
| **schema** | Parsing and validating notebook structure | spec |
| **model** | Runtime notebook model, dependency analysis | spec, schema |
| **engine** | Notebook and cell-level execution | model, interop |
| **errors** | Error construction and formatting | spec |
| **serialization** | Bidirectional JSON ↔ Notebook conversion | spec, schema |
| **interop** | Bridge to Genia interpreter | spec |
| **public** | Public API | all above |

### Design notes
- **No circular dependencies** between modules
- **spec** is pure; no dependencies
- **schema** is pure; no side effects
- **engine** depends on `interop` for operation execution
- **public** is a facade; implementation hides module organization

---

## 4. Execution Architecture

### 4.1 Full Notebook Execution (MVP)

```
executeNotebook(notebook: Notebook) → NotebookExecutionResult
  │
  ├─ Phase 1: Validate
  │  ├─ Parse schema (already done in spec)
  │  ├─ Check cell ID uniqueness
  │  ├─ Check forward refs (acyclicity)
  │  ├─ Check operation resolvability
  │  └─ Build DependencyGraph
  │     └─ on error: return ValidationError
  │
  ├─ Phase 2: Compute execution order
  │  ├─ Topological sort of cell dependencies
  │  └─ on error (cycle): return CycleError
  │
  ├─ Phase 3: Execute cells in order
  │  │
  │  └─ For each cell in executionOrder:
  │     ├─ if note_cell: record CellResultSkipped("note_cell")
  │     │
  │     ├─ if value_cell:
  │     │  └─ record CellResultSuccess(output: [value])
  │     │
  │     ├─ if pipeline_cell:
  │     │  ├─ Check depends_on cells ran successfully
  │     │  │  └─ if upstream failed: record CellResultError("UPSTREAM_FAILURE")
  │     │  │     and (halt OR continue)
  │     │  │
  │     │  ├─ Resolve external references (if any)
  │     │  │
  │     │  ├─ Delegate to Genia.executePipeline(pipeline)
  │     │  │  └─ returns: {success, output, error, nodeOutputs}
  │     │  │
  │     │  ├─ if success: record CellResultSuccess(output)
  │     │  │
  │     │  └─ if error: record CellResultError(error)
  │     │     and (halt OR continue)
  │     │
  │     ├─ if inspect_cell:
  │     │  ├─ Fetch output of source_cell
  │     │  │  └─ if source failed: record CellResultError("UPSTREAM_FAILURE")
  │     │  │
  │     │  └─ record CellResultSuccess(same output as source)
  │     │
  │     └─ if binding_cell:
  │        ├─ Fetch output of source_cell
  │        │  └─ if source failed: record CellResultError("UPSTREAM_FAILURE")
  │        │
  │        ├─ Register binding: bindings[binding_name] = output[0]
  │        │
  │        └─ record CellResultSuccess(same output as source)
  │
  └─ Phase 4: Return result
     ├─ cellResults (indexed by cell ID)
     ├─ bindings
     ├─ errors
     └─ executionOrder
```

### 4.2 Single-Cell (Re)Execution (future, but design for it)

```
executeSingleCell(notebook, cellId, options?) → CellExecutionResult
  │
  ├─ Validate:
  │  ├─ Cell exists
  │  ├─ All upstream dependencies can be resolved
  │  └─ (assume context from previous execution)
  │
  ├─ Execute:
  │  ├─ Re-run all upstream dependencies (if not cached)
  │  ├─ Execute target cell
  │  └─ Invalidate downstream cells (if any)
  │
  └─ Return result for target cell
```

**Caching strategy (future):**
- Cache cell outputs per execution run
- On re-execution: invalidate only affected descendants
- For MVP: no caching; always recompute full notebook

### 4.3 Error handling during execution

**Fail-fast (recommended MVP):**
- On first error, halt execution immediately
- Record error in cellResults
- Do not execute downstream cells (mark as "not_executed" or skip)

**Fail-through (future option):**
- Record error, continue executing independent cells
- Use DAG of cells to determine independence
- Requires more complex state management

**MVP choice**: Fail-fast (simpler, matches Jupyter semantics).

---

## 5. Dependency and Reference Design

### 5.1 Dependency Graph Construction

```
buildDependencyGraph(notebook: Notebook) → DependencyGraph | Error
  │
  ├─ For each cell:
  │  ├─ Extract direct dependencies:
  │  │  ├─ depends_on field (pipeline_cell)
  │  │  ├─ source_cell_id (inspect_cell, binding_cell)
  │  │  └─ implicit: prior cells
  │  │
  │  └─ Build DependencyNode
  │
  ├─ Validate each edge:
  │  ├─ Target cell exists (MISSING_CELL_REFERENCE error)
  │  ├─ Target cell appears earlier (FORWARD_REFERENCE error)
  │  └─ Record edge
  │
  ├─ Detect cycles:
  │  ├─ Run DFS on dependency edges
  │  └─ if found: return CYCLE_DETECTED error
  │
  ├─ Compute topological order:
  │  ├─ Kahn's algorithm (deterministic)
  │  └─ executionOrder = sorted cell IDs
  │
  └─ Return DependencyGraph
```

### 5.2 Reference Resolution (runtime)

```
resolveReference(context: ExecutionContext, ref: Reference) → ResolvedReference | Error
  │
  ├─ if ref.type == "cell_id":
  │  ├─ Look up cellId in cellResults
  │  ├─ if found: return output
  │  ├─ if not found: return MISSING_CELL_REFERENCE
  │  └─ if error: return UPSTREAM_FAILURE
  │
  └─ if ref.type == "binding_name":
     ├─ Look up binding_name in context.bindings
     ├─ if found: return value
     └─ if not found: return MISSING_BINDING
```

### 5.3 Acyclicity Guarantee

**Design principle:**
- All references must point backward in notebook order
- Parser enforces this on loads
- Validator catches forward references before execution

**Algorithm:**
```
for each cell at position i:
  for each reference in cell:
    target_pos = findCell(target).position
    if target_pos >= i:
      raise FORWARD_REFERENCE_ERROR
```

**Benefit**: Acyclicity is guaranteed by construction, not runtime detection.

---

## 6. Error Design

### 6.1 Error Classification

**Parse errors** (before validation):
- `PARSE_ERROR`: JSON/syntax error

**Validation errors** (before execution):
- `INVALID_SCHEMA`: Structure doesn't match spec
- `DUPLICATE_CELL_ID`: Two cells with same ID
- `FORWARD_REFERENCE`: Cell references a later cell
- `MISSING_CELL_REFERENCE`: Referenced cell doesn't exist
- `CYCLE_DETECTED`: Circular dependency (shouldn't happen if forward-ref check works)
- `UNKNOWN_OPERATION`: Operation not in registry
- `INVALID_BINDING_NAME`: Name conflicts with reserved words

**Execution errors** (during execution):
- `EXECUTION_FAILED`: Operation throws error
- `UPSTREAM_FAILURE`: Dependency cell failed
- `MISSING_BINDING`: Referenced binding not found

### 6.2 Error Construction

```
StructuredError factory methods:

makeParseError(message: string) → StructuredError
makeDuplicateCellIdError(cellIds: string[]) → StructuredError
makeForwardReferenceError(cellId: string, targetId: string) → StructuredError
makeUnknownOperationError(operation: string, cellId: string) → StructuredError
makeUpstreamFailureError(cellId: string, upstreamCellId: string) → StructuredError
makeExecutionFailedError(cellId: string, nodeId: string, originalError: any) → StructuredError
```

### 6.3 Error Reporting

```
NotebookExecutionResult (on error case)
├─ status: "error"
├─ error: StructuredError          [first/primary error]
├─ allErrors?: StructuredError[]   [all encountered, if fail-through mode]
└─ cellResults?: Map<...>          [partial results, if fail-through mode]
```

### 6.4 UI integration (not designed here, but structure supports)

Errors include:
- `code`: Machine-readable code for handling (e.g., show toast, highlight cell)
- `cellId`: Which cell to highlight
- `location.context`: Where in the cell (e.g., "node n2" for step-level error)
- `details`: Additional data for UI rendering

---

## 7. Serialization Path

### 7.1 Three-layer serialization model

```
Genia Data (JSON)
    ↓ (deserialize)
Spec Notebook (immutable, unvalidated)
    ↓ (parse + validate)
Model Notebook (validated, ready to execute)
    ↓ (execute)
ExecutionContext (results + bindings)
    ↓ (serialize results only)
Execution Report (JSON)
```

### 7.2 Deserialization: Genia Data → Spec Notebook

```
parseNotebook(data: any) → NotebookSpec | ParseError
  │
  ├─ Check data is object (not null, array, primitive)
  │
  ├─ Extract version
  │  └─ if missing: use default "1.0.0"
  │
  ├─ Extract metadata (optional)
  │
  ├─ Extract cells array
  │  └─ if missing or not array: error
  │
  ├─ For each cell object:
  │  ├─ Assert id: string
  │  ├─ Assert type: "note_cell" | ... | "binding_cell"
  │  ├─ Dispatch by type, extract type-specific fields
  │  │
  │  └─ Construct CellSpec (doesn't normalize/clean; raw data)
  │
  └─ Construct NotebookSpec
```

**Note**: Parsing is structural only. Does not validate references, operations, etc.

### 7.3 Validation: Spec Notebook → Model Notebook

```
validateNotebook(spec: NotebookSpec) → ModelNotebook | ValidationError
  │
  ├─ Check all cell IDs are unique
  │
  ├─ Build DependencyGraph (checks forward refs, operations, cycles)
  │
  ├─ Normalize pipeline structures (ensure all nodes/edges are present)
  │
  └─ Return ModelNotebook (ready for execution)
```

**Note**: Validation is comprehensive. Output is safe to execute.

### 7.4 Serialization: Spec Notebook → Genia Data

```
serializeNotebook(notebook: NotebookSpec) → GenieData
  │
  ├─ Export as-is (Spec is JSON-compatible by design)
  │
  └─ Return object (can be JSON.stringify'd)
```

**Invariant**: Round-trip guarantee — parse(serialize(nb)) == nb

### 7.5 How execution results are stored (separate from notebook)

```
ExecutionReport (serializable)
├─ notebookId?: string              [reference to notebook, optional]
├─ executedAt: ISO8601String
├─ cellResults: Map<cellId, CellResult>
│  ├─ CellResultSuccess: {status, output, executedAt}
│  ├─ CellResultError: {status, error}
│  └─ CellResultSkipped: {status, reason}
├─ bindings: Map<bindingName, GeniaValue>
└─ metadata: {...}
```

**Note**: Results are NOT merged back into NotebookSpec. Notebook remains immutable.

---

## 8. Runtime Integration with Genia

### 8.1 What Flowbook owns

- **Notebook structure**: Parsing, validation, cell ordering
- **Execution coordination**: Cell scheduling, dependency ordering
- **Execution context**: Cell results, bindings, error tracking
- **Reference resolution**: Name → value lookups
- **Error reporting**: Structured error formatting

### 8.2 What Genia interpreter owns

- **Operation semantics**: What `source`, `lines`, `sum`, etc. actually do
- **Pipeline execution**: Topological ordering inside a pipeline DAG
- **Type system**: Genia value types and coercions
- **Operation registry**: Discovering available operations

### 8.3 Integration interface

```
Genia interface (Flowbook's perspective):

interface GenieInterpreter {
  // Resolve an operation name
  resolveOperation(name: string) → OperationFn | null

  // Execute a pipeline (delegates graph execution)
  executePipeline(
    pipeline: {nodes, edges},
    input?: any
  ) → {
    success: boolean,
    output: any[],        // final node output
    error?: string,
    nodeOutputs: Map<nodeId, any[]>
  }

  // Query available operations
  listOperations() → string[]
}
```

**Design notes:**
- Flowbook does NOT implement `executePipeline`; it calls Genia
- Flowbook DOES handle cell-level execution, not Genia
- Genia is stateless (or manages its own state); Flowbook manages notebook state

### 8.4 Delegation pattern

```
Flowbook.executePipeline(cell: PipelineCellSpec, context: ExecutionContext)
  │
  ├─ Resolve external dependencies (from context.bindings)
  │
  ├─ Call Genia.executePipeline(cell.pipeline, externalInput)
  │
  ├─ Attach result to context.cellResults[cellId]
  │
  └─ Return result
```

**No operation code in Flowbook.** All operation logic stays in Genia.

---

## 9. MVP Boundaries

### 9.1 MVP requirements

**Must include:**
- Notebook parsing and schema validation
- Full notebook execution (cell-by-cell, in order)
- All 5 cell types (note, value, pipeline, inspect, binding)
- Dependency validation (no forward refs, no cycles)
- Structured error reporting
- Execution context (cell results, bindings)
- Single-pass execution (no caching or optimization)

**Code organization:**
- Spec types matching NOTEBOOK_SPEC.md exactly
- Schema module (parse + validate)
- Execution engine (coordinate cell execution)
- Error module (structured errors)
- Interop layer to Genia

### 9.2 Not in MVP

**Safe to defer:**
- Partial recomputation (re-run one cell, update downstream)
- Caching (store cell outputs between runs)
- Streaming result updates (push results to UI as they complete)
- Interactive cell re-editing (mid-execution)
- Cell groups / components (future abstraction)
- Advanced output hints (rich formatting)
- Multi-cell visualization (block diagram rendering)
- Undo/redo (requires immutable history)

**Why safe to defer:**
- Full recomputation is simple and correct
- Can optimize later without changing core semantics
- No architectural debt from deferring

### 9.3 Future extensions (design space)

**Partial recomputation:**
- Requires: memoization of cell outputs, invalidation DAG
- Changes: execution engine becomes incremental
- No spec changes needed

**Streaming UI updates:**
- Requires: notification callbacks from executor
- Changes: executor can yield results as cells complete
- No spec changes needed

**Parameterized operations:**
- Requires: operation parameter syntax and resolution
- Changes: spec adds parameter binding to operation string
- New spec section needed

**Typing:**
- Requires: type annotations on cells and operations
- Changes: validation becomes stronger
- New spec section needed

---

## 10. Risks and Drift Points

### 10.1 Potential drift from spec

| Risk | Mitigation |
|------|---|
| **Implicit state in execution engine** | Design ExecutionContext explicitly; no hidden caches |
| **Non-deterministic execution order** | Use Kahn's algorithm; document tie-breaking |
| **Genia semantics leaking into Flowbook** | Keep Flowbook free of operation logic; delegate all |
| **UI concerns in core** | No rendering, layout, or interaction code in modules |
| **Unbounded error recovery** | Fail-fast by default; no speculative "fixing" |
| **Silent reference failures** | Always return explicit error; no coercion |

### 10.2 Portability risks

| Risk | Mitigation |
|------|---|
| **Host-specific code in core** | All modules are pure functions + data structures |
| **Circular module dependencies** | Enforce DAG of module imports |
| **Language-specific idioms** | Document in pseudocode first; reference implementation in one host only |
| **Floating-point differences** | Delegate number handling to Genia; Flowbook doesn't coerce |
| **Timing-dependent behavior** | No threads, async, or event queues in core |

### 10.3 Validation gaps

**Schema validation might miss:**
- Binding names that shadow operation names (caught at runtime, not design time)
- Operation parameters that are malformed syntax (caught by Genia)
- Operation parameter type mismatches (caught by Genia)

**Mitigation:**
- Early validation is best-effort
- Errors are caught at execution time (acceptable for MVP)
- Future: add stronger operation parameter validation

### 10.4 Future questions to clarify

1. **What if a binding name conflicts with an operation?**
   - Spec says binding names must not conflict, but how is this enforced?
   - Design: validation checks binding names against registry
   - Implementation: pass available operations to validator

2. **What if Genia's operation registry changes between executions?**
   - A notebook might reference an operation that no longer exists
   - Design: validate operations on load, not on execution
   - Implementation: cache operation list at validation time

3. **How are `depends_on` fields actually used?**
   - Spec allows pipeline_cell to list external dependencies
   - But current executor doesn't resolve them
   - Design: `depends_on` is for documentation + validation only
   - Implementation: ensure referenced cells execute before pipeline runs

4. **What are the semantics of multiple sinks in a pipeline?**
   - Spec says "final node output" (singular)
   - What if there are multiple terminal nodes?
   - Design: topological order determines "final" node
   - Implementation: return output of last executed node

---

## Summary: Design Completeness Checklist

- [x] Internal data structures defined with fields, invariants, relationships
- [x] Module boundaries clear with dependencies acyclic
- [x] Execution architecture: full notebook, single-cell, error handling
- [x] Dependency model: acyclic, backward-ref only, explicit
- [x] Error design: structured, classified, host-portable
- [x] Serialization path: three-layer (data → spec → model → results)
- [x] Genia integration: clear ownership, delegation pattern
- [x] MVP: defined scope, deferrable features identified
- [x] Risks: identified and mitigated

**Status**: Ready for implementation in any host language.

---

**End of Architecture Design**
