# Project State

This file is the **final authority** on what is actually implemented now.

## 0) Current status

Implemented today:
- Repository scaffold
- AI workflow structure
- Prompt pipeline templates
- Documentation and test placeholders
- Flow graph model (FlowNode, FlowEdge, FlowGraph) and executor
- Topological graph execution with per-node output recording
- Basic operation registry (source, lines, map(parse_int), sum)

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
- None yet

Not implemented:
- Notebook runtime (no cell execution ordering)
- Binding system (no binding_cell execution)
- Inspector (no inspect_cell rendering)
- Multi-cell notebooks (no composition system)
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

This scaffold provides process and structure only.
It does not define your project's actual product semantics yet.

## 4) How to evolve this file

Whenever a feature becomes real:
- add it here
- mark whether it is implemented, partial, or not implemented
- keep this file narrower and more truthful than the README
