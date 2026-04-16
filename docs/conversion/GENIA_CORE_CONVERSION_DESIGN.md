# Genia Core Conversion Design

## Design Goals

1. Move Flowbook notebook semantics into Genia-owned code.
   - Notebook validation, cell execution, dependency ordering, binding registration, inspect behavior, and structured errors belong to Genia core.

2. Keep the host/Genia boundary thin.
   - The host sends JSON/Genia-data-compatible notebook payloads.
   - The host receives JSON/Genia-data-compatible validation and execution results.
   - The host does not participate in semantic decisions.

3. Preserve the current React app as a temporary host shell.
   - The app remains responsible for rendering, editing, selection state, and display formatting.
   - The app stops owning graph execution semantics.

4. Reuse the existing repo design where it already answers the problem.
   - `docs/book/NOTEBOOK_SPEC.md` defines notebook and cell semantics.
   - `docs/architecture/CORE_ARCHITECTURE.md` defines the core model, execution architecture, and error approach.
   - `src/genia/flowbook` is the starting package for Phase 1, not a parallel redesign.

5. Provide a compatibility path from the current graph prototype to notebook execution.
   - The existing graph editor becomes a temporary editor for a single `pipeline_cell`.
   - A small adapter wraps that pipeline in notebook-shaped data for Genia execution.

## Proposed Module Layout

### 1. Genia-side layout

Phase 1 should keep the Genia-owned core under `src/genia/flowbook` and tighten the file responsibilities so the package cleanly matches the architecture doc.

```text
src/genia/flowbook/
  __init__.py
  api.py             # Public entrypoints for host and tests
  model.py           # Notebook, cell, pipeline, result, and error dataclasses
  schema.py          # Parse + validate notebook-shaped Genia data
  references.py      # Cell dependency graph + backward-reference validation
  executor.py        # Notebook cell execution orchestration
  serialize.py       # Notebook model -> JSON-compatible Genia data
  errors.py          # Structured error builders and exception wrappers
  interop.py         # Genia pipeline runtime interface and adapter
```

Role by module:
- `api.py`
  - Stable public surface for `load`, `validate`, `execute_notebook`, `execute_cell`, `dump`, and `list_capabilities`.
  - Hosts import this layer only.
- `model.py`
  - Canonical immutable notebook structures.
  - Canonical result and error payload structures.
- `schema.py`
  - Input parsing and schema validation for raw Genia/JSON-shaped notebook data.
  - No execution.
- `references.py`
  - Dependency extraction for `depends_on` and `source_cell_id`.
  - Backward-reference enforcement.
  - Cell-level topological order computation.
- `executor.py`
  - Cell-by-cell notebook execution.
  - Delegates `pipeline_cell` execution to the Genia runtime interface.
  - Does not fall back to host TypeScript execution.
- `interop.py`
  - Defines the runtime-facing interface for pipeline execution and operation discovery.
  - Holds the real Genia adapter used by notebook execution.
- `serialize.py`
  - Notebook model -> notebook-shaped data.
  - No UI formatting.
- `errors.py`
  - Shared structured error constructors and Flowbook exception classes.

### 2. Host-side layout

Phase 1 should add a narrow bridge layer in TypeScript and keep UI files focused on rendering.

```text
src/
  bridge/
    flowbook.ts      # Host-side bridge client: executeNotebook, executeCell, listCapabilities
    types.ts         # NotebookData, request/response DTOs mirroring Genia schema
    adapters.ts      # Temporary graph <-> notebook adapter for the current prototype
  model/
    notebook.ts      # Temporary host mirror types for notebook-shaped editor state
  ui/
    ...              # Existing rendering components
  App.tsx            # Temporary host shell wired to bridge API instead of executeGraph
```

Role by module:
- `bridge/types.ts`
  - DTOs that mirror Genia-owned shapes exactly.
  - No host-only semantic fields.
- `bridge/flowbook.ts`
  - The only host entrypoint that invokes Flowbook core.
  - Returns execution/validation results to the app.
- `bridge/adapters.ts`
  - Temporary compatibility helpers that wrap the current `FlowGraph` into a minimal notebook with one `pipeline_cell`.
  - This file is transitional and removed once the host edits notebook state directly.
- `model/notebook.ts`
  - Optional host mirror of the notebook DTO for editor state.
  - Must remain shape-compatible with Genia data, not a separate semantic model.

### 3. Existing files that lose authority

- [src/model/types.ts](/Users/m0smith/projects/genia-flowbook/src/model/types.ts)
  - Stops being the product-level domain model.
- [src/model/index.ts](/Users/m0smith/projects/genia-flowbook/src/model/index.ts)
  - Becomes helper code for temporary editor DTO creation only, or is removed later.
- [src/engine/executor.ts](/Users/m0smith/projects/genia-flowbook/src/engine/executor.ts)
  - Removed from the production execution path.
- [src/engine/operations.ts](/Users/m0smith/projects/genia-flowbook/src/engine/operations.ts)
  - Removed from the production execution path.
- [src/App.tsx](/Users/m0smith/projects/genia-flowbook/src/App.tsx)
  - Stops calling `executeGraph` directly.

## Core Data Shapes

These shapes must stay aligned with `NOTEBOOK_SPEC.md` and `CORE_ARCHITECTURE.md`.

### 1. Notebook input shape

```ts
type NotebookData = {
  version: string;
  metadata?: {
    author?: string;
    description?: string;
    created_at?: string;
    source?: string;
  };
  cells: CellData[];
};
```

```ts
type CellData =
  | NoteCellData
  | ValueCellData
  | PipelineCellData
  | InspectCellData
  | BindingCellData;
```

```ts
type CellBaseData = {
  id: string;
  type: "note_cell" | "value_cell" | "pipeline_cell" | "inspect_cell" | "binding_cell";
  metadata?: {
    label?: string;
    custom?: Record<string, unknown>;
  };
};
```

```ts
type NoteCellData = CellBaseData & {
  type: "note_cell";
  content: string;
};
```

```ts
type ValueCellData = CellBaseData & {
  type: "value_cell";
  value: GeniaValue;
};
```

```ts
type PipelineCellData = CellBaseData & {
  type: "pipeline_cell";
  pipeline: {
    nodes: {
      id: string;
      type: "source" | "transform" | "sink";
      operation: string;
      x?: number;
      y?: number;
    }[];
    edges: {
      id: string;
      from: string;
      to: string;
    }[];
  };
  depends_on?: string[];
};
```

```ts
type InspectCellData = CellBaseData & {
  type: "inspect_cell";
  source_cell_id: string;
  format?: string;
};
```

```ts
type BindingCellData = CellBaseData & {
  type: "binding_cell";
  binding_name: string;
  source_cell_id: string;
};
```

### 2. Execution context shape inside Genia

Phase 1 should continue to use the architecture doc’s separation:
- immutable notebook model
- computed dependency graph
- mutable execution context

Internal Genia shape:

```text
ExecutionContext
  notebook: Notebook
  cell_results: Map<cell_id, CellResult>
  bindings: Map<binding_name, GeniaValue>
  errors: Map<cell_id, StructuredError>
  execution_order: string[]
  halted: boolean
```

The host must never own this structure.

### 3. Temporary compatibility notebook shape

To support the current graph prototype, the host bridge may wrap the current graph in a single-cell notebook.

```ts
type PrototypeGraphNotebook = {
  version: "1.0.0";
  cells: [
    {
      id: "main-pipeline";
      type: "pipeline_cell";
      pipeline: {
        nodes: PipelineNodeData[];
        edges: PipelineEdgeData[];
      };
    }
  ];
};
```

This is a compatibility wrapper only. It is not a new product semantic.

## Bridge API Contract

The bridge contract stays data-only and uses explicit entrypoints.

### 1. Host -> Genia requests

```ts
type ExecuteNotebookRequest = {
  notebook: NotebookData;
  options?: {
    fail_fast?: boolean;
  };
};
```

```ts
type ExecuteCellRequest = {
  notebook: NotebookData;
  cell_id: string;
};
```

```ts
type ValidateNotebookRequest = {
  notebook: NotebookData;
};
```

```ts
type CapabilitiesRequest = {};
```

Rules:
- The host sends notebook-shaped data only.
- The host does not send operation code.
- The host does not send graph execution hints.
- The host does not send JS callbacks for validation or execution.

### 2. Genia -> Host responses

```ts
type ValidateNotebookResponse =
  | { ok: true; notebook_valid: true }
  | { ok: false; notebook_valid: false; error: StructuredErrorData };
```

```ts
type ExecuteNotebookResponse = {
  status: "success" | "error";
  notebook_valid: boolean;
  execution_order: string[];
  cell_results: Record<string, CellResultData>;
  bindings: Record<string, GeniaValue>;
  error?: StructuredErrorData;
};
```

```ts
type ExecuteCellResponse = {
  notebook_valid: boolean;
  cell_result: CellResultData;
  error?: StructuredErrorData;
};
```

```ts
type CapabilitiesResponse = {
  notebook_version: string;
  operations: string[];
};
```

### 3. Execution entrypoints

Genia public entrypoints:
- `flowbook.load(data) -> Notebook`
- `flowbook.validate(data) -> bool | StructuredError`
- `flowbook.execute(data, interpreter=None, fail_fast=True) -> ExecutionResult`
- `flowbook.execute_cell(data, cell_id, interpreter=None) -> CellResult`
- `flowbook.dump(notebook) -> dict`
- `flowbook.list_capabilities(interpreter=None) -> CapabilitiesResponse`

Host bridge entrypoints:
- `executeNotebook(request: ExecuteNotebookRequest): Promise<ExecuteNotebookResponse>`
- `executeCell(request: ExecuteCellRequest): Promise<ExecuteCellResponse>`
- `validateNotebook(request: ValidateNotebookRequest): Promise<ValidateNotebookResponse>`
- `listCapabilities(): Promise<CapabilitiesResponse>`
- `prototypeGraphToNotebook(graph: FlowGraph): NotebookData`

The bridge must not expose `executeGraph`.

## Error and Result Shapes

### 1. Structured error shape

The repo already defines the error model in `CORE_ARCHITECTURE.md` and `src/genia/flowbook/errors.py`. Phase 1 should standardize on the following data shape across the bridge:

```ts
type StructuredErrorData = {
  type: "error";
  code:
    | "PARSE_ERROR"
    | "INVALID_SCHEMA"
    | "DUPLICATE_CELL_ID"
    | "UNKNOWN_OPERATION"
    | "CYCLE_DETECTED"
    | "FORWARD_REFERENCE"
    | "MISSING_CELL_REFERENCE"
    | "INVALID_BINDING_NAME"
    | "UPSTREAM_FAILURE"
    | "EXECUTION_FAILED";
  message: string;
  location: {
    step: "parsing" | "validation" | "execution";
    context: string;
  };
  cell_id?: string;
  details: Record<string, unknown>;
  timestamp?: string;
};
```

Requirements:
- All bridge errors are structured.
- Validation and execution do not return host-shaped string errors as the primary error contract.
- The host may derive display text, but it does not reinterpret error codes.

### 2. Cell result shape

```ts
type CellResultData =
  | CellResultSuccessData
  | CellResultSkippedData
  | CellResultErrorData;
```

```ts
type CellResultSuccessData = {
  status: "success";
  cell_id: string;
  cell_type: CellData["type"];
  output: GeniaValue[];
  executed_at?: string;
  node_outputs?: Record<string, GeniaValue[]>;
};
```

```ts
type CellResultSkippedData = {
  status: "skipped";
  cell_id: string;
  reason: string;
};
```

```ts
type CellResultErrorData = {
  status: "error";
  cell_id: string;
  error: StructuredErrorData;
  executed_at?: string;
};
```

### 3. Notebook execution result shape

```ts
type NotebookExecutionResultData = {
  status: "success" | "error";
  notebook_valid: boolean;
  cell_results: Record<string, CellResultData>;
  bindings: Record<string, GeniaValue>;
  execution_order: string[];
  error?: StructuredErrorData;
};
```

Semantics:
- `status: "error"` means notebook execution did not complete successfully.
- `cell_results` remains populated for cells executed before failure.
- `bindings` contains only bindings successfully registered before failure.
- `execution_order` reflects Genia-owned cell ordering.

## Migration Stages

Phase 1 should move in small, explicit stages.

### Stage 0: Freeze the current authority boundary

State:
- TS graph executor and operation map are still the runnable path.
- `src/genia/flowbook` exists but is not yet the product authority.

Goal:
- Document that `src/engine/*` is prototype-only.
- Prevent new notebook semantics from being added to TypeScript.

### Stage 1: Make `src/genia/flowbook` the only notebook authority

Changes:
- Keep `model.py`, `schema.py`, `references.py`, `executor.py`, `serialize.py`, and `errors.py` as the canonical Phase 1 core.
- Add `interop.py` for pipeline-runtime integration.
- Remove the default fallback in `src/genia/flowbook/executor.py` that calls `src.engine.executeGraph`.

Result:
- Genia-owned notebook execution path exists without dependence on the React host runtime.

### Stage 2: Add the host bridge

Changes:
- Add `src/bridge/types.ts` and `src/bridge/flowbook.ts`.
- Define request/response DTOs that mirror Genia shapes exactly.
- Add `validateNotebook`, `executeNotebook`, and `executeCell` bridge calls.

Result:
- The React host has one narrow integration seam.

### Stage 3: Introduce the temporary graph-to-notebook adapter

Changes:
- Add `prototypeGraphToNotebook(graph)` in `src/bridge/adapters.ts`.
- Wrap the current `FlowGraph` in a notebook with one `pipeline_cell`.

Result:
- The current graph canvas can execute through the notebook path without becoming the notebook model.

### Stage 4: Rewire the React app

Changes:
- `App.tsx` stops importing `executeGraph`.
- `App.tsx` calls the bridge with notebook-shaped data.
- Execution results displayed in the UI come from `CellResultData` and `NotebookExecutionResultData`.

Result:
- The current UI remains visually similar, but execution authority has moved to Genia.

### Stage 5: Shift host state from graph-first to notebook-first

Changes:
- Replace top-level `FlowGraph` state in `App.tsx` with notebook-shaped state or a notebook-shaped editor model.
- Keep the existing canvas as the editor for the selected `pipeline_cell`.

Result:
- The host now edits the correct top-level artifact.

### Stage 6: Retire the prototype runtime files

Changes:
- Remove `src/engine/executor.ts` and `src/engine/operations.ts` from production wiring.
- Reduce `src/model/types.ts` and `src/model/index.ts` to bridge/editor helpers or delete them if no longer needed.

Result:
- No semantic execution path remains in TypeScript.

## Compatibility Notes for Current React Host

1. The current canvas remains useful.
   - It already edits `nodes`, `edges`, `x`, and `y`.
   - Those map directly to the `pipeline` field inside a `pipeline_cell`.

2. The current default graph becomes a default notebook fixture.
   - The existing `source -> lines -> map(parse_int) -> sum` example should be wrapped as one `pipeline_cell`.
   - The host does not keep it as a standalone graph document.

3. `App.tsx` can migrate without a UI redesign.
   - Keep selection state, connect intent, and toolbar interactions unchanged.
   - Change only the data source and execution call path.

4. Current node output display remains viable.
   - The result table can continue to render per-node outputs if Genia returns `node_outputs` for `pipeline_cell` execution.
   - This is presentation, not semantic ownership.

5. Host mirror types are allowed only as DTO mirrors.
   - If TypeScript keeps `NotebookData` or `PipelineCellData`, those must match Genia shapes exactly.
   - A divergent TS domain model is not allowed.

6. The current graph helpers are transitional only.
   - `createNode`, `createEdge`, and `createGraph` can survive briefly as editor helpers.
   - They must not imply that `FlowGraph` is the notebook runtime model.

7. The host should surface bridge failures directly.
   - If notebook validation or execution fails, the UI shows Genia’s structured error.
   - The host does not fall back to local execution.

## Open Questions

1. What is the concrete runtime transport from the React host to Genia core in this repo?
   - The design requires a bridge, but the repository does not yet define whether that bridge is in-process, HTTP, worker-based, or test-harness-only.
   - This is unavoidable because it affects where `src/bridge/flowbook.ts` calls land.

2. What is the authoritative Genia pipeline executor that replaces the current fallback from `src/genia/flowbook/executor.py` to `src.engine.executeGraph`?
   - The design requires Genia ownership, but the current repo does not yet expose that concrete runtime adapter.
   - Phase 1 cannot be complete until that adapter exists.
