# Project State

This file is the **final authority** on what is actually implemented now.

## 0) Current status

Implemented today:
- Repository scaffold
- AI workflow structure
- Prompt pipeline templates
- Documentation and test placeholders
- Flow graph model (FlowNode, FlowEdge, FlowGraph) for the temporary React host editor only
- Flowbook core boundary in TypeScript for notebook-shaped validation/execution requests
- In-process host bridge that routes the React demo through notebook-shaped Flowbook core data
- Compatibility notebook wrapper for the current graph prototype (`FlowGraph` -> single `pipeline_cell`)
- Compatibility pipeline runtime behind the Flowbook core boundary for the current demo path
- Topological pipeline execution with per-node output recording for the default demo path
- Compatibility operation registry for the default demo path (source, lines, map(parse_int), sum)
- Black-box tests for the core/bridge execution boundary and structured error shape

Specification and design (not yet implemented):
- Flowbook Notebook Core specification (see `docs/book/NOTEBOOK_SPEC.md`)
  - Notebook structure (metadata, cell ordering)
  - Five cell types: note_cell, value_cell, pipeline_cell, inspect_cell, binding_cell
  - Execution model (cell order, error isolation, determinism)
  - Reference system (cell ID, binding name, acyclicity rules)
  - Error model (structured errors, cell-level vs step-level)
  - Serialization format (JSON-compatible Genia data)
- Internal architecture design (see `docs/architecture/CORE_ARCHITECTURE.md`)
  - Core data structures (Notebook, Cell, Pipeline, ExecutionContext, DependencyGraph)
  - Module boundaries (schema, model, engine, errors, serialization, interop)
  - Execution architecture (full notebook, single-cell, error handling)
  - Dependency/reference model (acyclic DAG with backward-ref enforcement)
  - Error design (structured, classified, portable)
  - Serialization path (3-layer: Genia data → Spec → Model → Results)
  - Genia runtime integration (clear ownership)
  - MVP scope and deferrable features

Partial:
- Notebook runtime boundary exists for the current TypeScript demo path, but only as a Phase 1 compatibility layer
- React app no longer calls the graph executor as the primary runtime entrypoint
- The current demo executes via notebook-shaped data and a single `pipeline_cell`
- The repository now documents the React app as a temporary host shell rather than the product semantic implementation

Not implemented:
- Genia-owned runtime transport between the React host and `src/genia/flowbook`
- Full replacement of the temporary compatibility runtime with a real Genia interpreter/runtime adapter
- Browser-native Genia execution
- Notebook cells as first-class editable objects in the active React host path
- Multi-cell notebook execution in the active React host path
- Full notebook UI/editor for all five cell types
- Parameter resolution in operations
- Any feature not explicitly listed above

## 1) Source of truth rule

If any file disagrees with this file, **this file wins**.

## 2) Current workflow

The repository uses:
- pre-flight review
- spec prompt
- design prompt
- implementation prompt
- test prompt
- docs sync prompt
- audit / truth review prompt

## 3) Limitations

The current React app is a temporary host shell.

The active browser demo path preserves an old graph prototype by routing it through a notebook-shaped compatibility boundary.

That compatibility path is not the final Genia runtime.

Flowbook product semantics are defined by the notebook/core docs and must continue moving toward Genia-owned execution.

## 4) How to evolve this file

Whenever a feature becomes real:
- add it here
- mark whether it is implemented, partial, or not implemented
- keep this file narrower and more truthful than the README
