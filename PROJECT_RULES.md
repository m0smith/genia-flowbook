# Project Rules

This file defines semantics, constraints, invariants, and behavioral rules for the project.

See `docs/book/NOTEBOOK_SPEC.md` for the complete Flowbook Notebook Core specification.

## Global rules

- Explicit behavior beats implicit behavior.
- Public behavior must be documented only after implementation and tests.
- Error cases must be specified, not inferred.
- Backward compatibility decisions must be explicit.
- Platform-specific behavior must be clearly marked.
- Flow-first design: every element represents a Genia runtime concept.
- No hidden semantics: all data flow is explicit.

## Invariants (Flowbook Notebook)

Core invariants that MUST always hold:

- **Acyclicity**: No circular dependencies between cells or within pipelines
- **Backward references only**: A cell may only reference cells that appear before it in notebook order
- **Unique identifiers**: All cell IDs within a notebook must be unique
- **Explicit data flow**: All data flows through pipelines; no implicit coercion or defaults
- **Deterministic execution**: Same notebook input → same outputs in same order, always
- **Error isolation**: Errors in one cell do not corrupt independent cells
- **Composability**: Cells compose via pipelines; no non-composable control structures
- **No mutation**: Notebook execution does not mutate the notebook structure
- **Valid Genia data**: A notebook is serializable as valid Genia data (JSON-compatible)

### Execution order invariants
- Cells execute in notebook order, top to bottom
- Within a pipeline (pipeline_cell), nodes execute in topological order
- A cell is not re-executed unless explicitly requested by the runtime
- If a cell fails, dependent cells are not executed (fail-fast by default)

### Reference invariants
- `depends_on` fields reference only earlier cells
- `source_cell_id` references only earlier cells
- All referenced cells must exist (no dangling references)
- Binding names must be unique within a notebook
- Binding names must not conflict with reserved operation names

### Pipeline invariants
- A pipeline must be a DAG (no cycles allowed)
- All node IDs within a pipeline must be unique
- All edge endpoints must reference existing nodes
- All operation names must be resolvable in the Genia operation registry

## Naming / conventions

### Cell IDs
- Format: alphanumeric identifier (e.g., `"c1"`, `"notebook-item-5"`, `"analysis_step_1"`)
- Must be unique within a notebook
- Case-sensitive

### Binding names
- Format: alphanumeric + underscore (must start with letter or underscore)
- Must not conflict with built-in operation names (e.g., `source`, `lines`, `sum`)
- Must not conflict with reserved keywords (reserved for future use)
- Case-sensitive
- Must be unique within a notebook

### Operation names
- Format: alphanumeric with optional parameters (e.g., `"source"`, `"map(parse_int)"`)
- Must be registered in the Genia interpreter's operation registry
- Case-sensitive

## Failure model

### Failure reporting
All errors are structured with:
- `type`: Always `"error"`
- `code`: Machine-readable error code (e.g., `"UNKNOWN_OPERATION"`)
- `message`: Human-readable description
- `cell_id`: ID of the cell where the error occurred (optional for parse errors)
- `location`: Where in the process (parsing, validation, execution) the error occurred
- `details`: Additional context-specific information

### Failure propagation
- **Parse errors**: Parsing fails; no execution occurs
- **Validation errors**: Validation fails; no execution occurs
- **Execution errors**: Cell execution fails; dependent cells are not executed
  - Upstream failures cascade to dependent cells
  - Independent cells may continue (implementation choice; default: halt-fast)

### Error isolation
- An error in one cell MAY affect dependent cells (via cascading halt)
- But errors do NOT corrupt the notebook or other independent cells
- Failed cells retain their error status; re-execution is needed to recover
