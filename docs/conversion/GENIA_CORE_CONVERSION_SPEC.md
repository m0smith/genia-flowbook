# Genia Core Conversion Spec

## Problem Statement

Flowbook is specified as a Genia notebook system, but the current runnable implementation is a host-owned TypeScript graph editor and graph executor. The browser app currently defines pipeline structure, operation availability, pipeline execution order, execution results, and the default runnable example. That ownership is backwards.

`PROJECT_STATE.md` says the notebook runtime is not implemented and the current implementation is limited to a flow graph model plus executor. `docs/book/NOTEBOOK_SPEC.md` and `docs/architecture/CORE_ARCHITECTURE.md` define a different target: notebook semantics belong to Flowbook core, pipeline semantics belong to Genia, and the host remains a renderer/editor. Phase 1 corrects that direction without replacing the current browser app.

## Current State vs Target State

| Area | Current State | Target State |
|---|---|---|
| Primary data model | `src/model/types.ts` defines `FlowNode`, `FlowEdge`, `FlowGraph` as the app's core domain model | Genia-owned notebook model is primary: notebook, cells, pipeline, execution context, structured errors |
| Notebook semantics | Not represented in the TS app | Owned by Genia core exactly as specified in `NOTEBOOK_SPEC.md` |
| Pipeline semantics | `src/engine/executor.ts` performs DAG validation, topological sort, parent input flattening, final output selection, and error shaping | Owned by Genia interpreter/core boundary, not by the React host |
| Operation registry | `src/engine/operations.ts` hard-codes `source`, `lines`, `map(parse_int)`, `sum` | Owned by Genia |
| Cell execution | Not present in the TS app | Owned by Genia core notebook executor |
| Host UI | React app edits and runs a graph directly | React app edits notebook/pipeline data and renders Genia-owned execution results |
| Existing Genia-side core | `src/genia/flowbook` exists, but `src/genia/flowbook/executor.py` falls back to `src.engine.executeGraph` | `src/genia/flowbook` executes through a Genia-owned pipeline executor only |

## Genia-Owned Responsibilities

The following responsibilities must move into Genia ownership and stop being defined by the current TypeScript host.

1. Notebook schema and validation.
   - `version`, `cells`, notebook metadata, cell metadata, and all five cell types are Genia-side structures.
   - Validation of unique cell IDs, non-empty notebooks, backward-only references, binding-name rules, and structured validation errors belongs to Genia core.

2. Cell semantics.
   - `note_cell` is non-executable and yields a skipped result.
   - `value_cell` yields `[value]`.
   - `pipeline_cell` executes a pipeline plus declared dependencies.
   - `inspect_cell` returns the referenced cell output without transforming it.
   - `binding_cell` registers a binding in notebook execution context and returns the referenced output.

3. Notebook execution ordering.
   - Cell dependency analysis, execution order, fail-fast behavior, upstream failure handling, and execution context state belong to Genia core.
   - The host must not decide which cells are executable, skipped, or failed.

4. Pipeline execution semantics.
   - DAG validation, pipeline topological ordering, node input collection rules, final output rules, and operation dispatch belong to Genia.
   - The behavior currently implemented in [src/engine/executor.ts](/Users/m0smith/projects/genia-flowbook/src/engine/executor.ts) must not remain authoritative.

5. Operation registry and operation meaning.
   - The host must not hard-code the operation set.
   - [src/engine/operations.ts](/Users/m0smith/projects/genia-flowbook/src/engine/operations.ts) is temporary host scaffolding and must stop defining product semantics.

6. Execution result model.
   - Success, error, skipped states, structured errors, bindings, cell results, node outputs, and execution order belong to Genia core.
   - The host only displays returned results.

7. Serialization and deserialization.
   - Notebook loading, validation, and JSON-compatible Genia serialization belong to Genia core.
   - The host exchanges notebook-shaped data, not host-only graph objects as the primary artifact.

8. Reference resolution.
   - `depends_on`, `source_cell_id`, and `binding_name` resolution rules belong to Genia core.
   - The host must not invent parallel reference logic.

9. Canonical pipeline and notebook types.
   - `FlowGraph` is not the product-level source of truth.
   - If TypeScript keeps local mirror types for transport, they must be treated as bridge DTOs that mirror Genia-owned schema exactly.

## Host-Owned Responsibilities

The following responsibilities remain host-only in Phase 1.

1. Rendering and interaction.
   - SVG canvas layout, node boxes, edges, selection state, toolbar actions, click handling, and result presentation remain in the React app.
   - Files under [src/ui](/Users/m0smith/projects/genia-flowbook/src/ui) remain host-owned.

2. Ephemeral editor state.
   - Selection, connection intent, local draft edits, viewport coordinates, and temporary UI affordances remain host concerns.
   - `x` and `y` coordinates remain host-authored layout metadata even when embedded in pipeline data.

3. Transport and adaptation.
   - The host may serialize user edits into notebook-shaped data and submit execution requests to Genia.
   - The host may deserialize Genia responses into view models for display.

4. Notebook editing workflow.
   - Adding a cell, reordering cells, editing markdown, drawing pipeline nodes and edges, and choosing an inspect format are host editing actions.
   - The host performs these actions by mutating notebook data structures, not by redefining semantics.

5. Presentation-only formatting.
   - Inspect rendering mode selection such as raw/table/json display remains a UI concern.
   - The meaning of `inspect_cell` output does not move to the host.

6. Temporary host shell.
   - The current React app remains the temporary editor/renderer for Phase 1.
   - Phase 1 does not require replacing React or building a browser-native Genia runtime.

## Bridge Contract

Phase 1 requires a narrow contract between the host UI and Genia core. The contract is data-oriented and one-directional on semantics: the host sends notebook data and receives validated execution state.

### 1. Host to Genia

The host sends notebook-shaped data that matches the notebook spec.

```ts
type ExecuteNotebookRequest = {
  notebook: NotebookData;
  options?: {
    fail_fast?: boolean;
    target_cell_id?: string;
  };
};
```

Rules:
- `NotebookData` matches the Genia-owned notebook schema exactly.
- The host does not send host-only wrapper types as the canonical payload.
- Pipeline node coordinates are allowed as UI metadata inside the notebook payload.
- The host does not send executable JavaScript functions, operation implementations, or host-defined semantic callbacks.

### 2. Genia to Host

Genia returns validated execution state.

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

`CellResultData` must preserve:
- `status`: `success` | `error` | `skipped`
- `cell_id`
- `cell_type`
- `output` for successful executable cells
- `reason` for skipped cells
- `error` for failed cells
- optional pipeline `node_outputs` when the cell is a `pipeline_cell`

### 3. Optional host support query

The host may ask Genia for editor-support metadata that does not redefine semantics.

```ts
type GeniaCapabilitiesResponse = {
  operations: string[];
  notebook_version: string;
};
```

This query is read-only. It does not move operation ownership back to the host.

### 4. Prohibited bridge behavior

The bridge must not:
- ask the host to topologically sort pipelines
- ask the host to validate notebook references as the source of truth
- ask the host to decide final pipeline outputs
- ask the host to define operation behavior
- ask the host to emulate notebook execution because Genia is unavailable

If Genia is unavailable, execution is unavailable. The host may display an error state but must not silently substitute host semantics.

## Phase 1 Scope

Phase 1 is a semantic ownership correction, not a full product rewrite.

1. Make the notebook model authoritative on the Genia side.
   - The authoritative runtime path is `Notebook -> validation -> dependency analysis -> notebook execution -> structured results`.

2. Remove host ownership of pipeline execution semantics.
   - The TypeScript graph executor and operation registry stop being the product runtime authority.
   - The fallback in [src/genia/flowbook/executor.py](/Users/m0smith/projects/genia-flowbook/src/genia/flowbook/executor.py) to `src.engine.executeGraph` must be removed or explicitly isolated as non-authoritative test scaffolding outside the product path.

3. Keep the React app as a temporary host editor/renderer.
   - The browser app continues to render and edit.
   - The browser app stops defining notebook or pipeline semantics.

4. Reconcile the graph-only app with all five notebook cell types.
   - `note_cell`: editable text cell in notebook order; never executed by host.
   - `value_cell`: literal Genia value cell; host edits value data only.
   - `pipeline_cell`: graph editor remains the host view for the embedded pipeline only.
   - `inspect_cell`: host renders Genia-returned output for `source_cell_id`.
   - `binding_cell`: host edits `binding_name` and `source_cell_id`; binding behavior is Genia-side only.

5. Use notebook data as the integration artifact.
   - The top-level host state must be notebook-shaped or losslessly convertible to notebook-shaped data.
   - A bare `FlowGraph` is insufficient as the product document model because it cannot represent notebook ordering or four of the five required cell types.

## Explicit Non-Goals

1. Rewriting the browser UI.
2. Designing a browser-native Genia interpreter.
3. Adding new notebook semantics beyond `NOTEBOOK_SPEC.md`.
4. Expanding the operation system beyond what Genia already defines.
5. Solving caching, streaming, multiplayer editing, or partial recomputation.
6. Finalizing a long-term desktop, web, or server deployment architecture.
7. Treating the current TS graph executor as a permanent compatibility layer.

## Risks / Drift Points

1. `FlowGraph` remains treated as the real domain model.
   - This blocks notebook ordering, `note_cell`, `value_cell`, `inspect_cell`, and `binding_cell`.

2. `src/engine/operations.ts` remains the effective operation registry.
   - That keeps product semantics in the host shell.

3. `src/engine/executor.ts` remains the effective pipeline runtime.
   - That preserves host-defined execution ordering and error behavior.

4. `src/genia/flowbook/executor.py` continues to delegate back into `src.engine`.
   - That creates a false appearance of Genia ownership while the host still controls semantics.

5. The React app continues to run a graph directly from [src/App.tsx](/Users/m0smith/projects/genia-flowbook/src/App.tsx).
   - That reinforces the wrong top-level abstraction.

6. DTOs drift from the notebook spec.
   - If a TS transport type differs from Genia notebook schema, the host will reintroduce semantic ownership by translation.

7. Inspect and binding behavior gets reimplemented in the host for convenience.
   - That would split notebook execution semantics across layers.

8. Documentation continues to describe Flowbook as if the notebook core were already the active runtime.
   - That would repeat the same drift the conversion is meant to fix.

## Definition of Done

Phase 1 is done only when all of the following are true.

1. The authoritative executable document model is the notebook model, not `FlowGraph`.

2. Genia core owns execution of all five cell types exactly as specified:
   - `note_cell`
   - `value_cell`
   - `pipeline_cell`
   - `inspect_cell`
   - `binding_cell`

3. Genia core owns pipeline execution semantics.
   - No production execution path depends on [src/engine/executor.ts](/Users/m0smith/projects/genia-flowbook/src/engine/executor.ts) or [src/engine/operations.ts](/Users/m0smith/projects/genia-flowbook/src/engine/operations.ts) as semantic authorities.

4. The React app acts as a host renderer/editor only.
   - It sends notebook-shaped data to Genia.
   - It renders Genia-returned results.
   - It does not decide execution order, operation behavior, binding behavior, inspect behavior, or final outputs.

5. The bridge contract is implemented and narrow.
   - Request payloads are notebook-shaped.
   - Response payloads contain structured execution results.
   - No semantic fallback to host execution exists.

6. The current graph editor is re-scoped as a `pipeline_cell` editor, not the whole notebook runtime.

7. Tests verify the ownership boundary.
   - Notebook execution tests run against Genia core.
   - Host tests verify rendering/editing and contract wiring only.
   - No host test is the source of truth for notebook semantics.

8. Repo docs describe the current truth accurately.
   - `PROJECT_STATE.md` reflects the active runtime path.
   - Notebook docs describe only behavior that the Genia-owned path actually implements.
