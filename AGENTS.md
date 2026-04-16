# Genia Flowbook – Copilot Instructions

## Purpose
Flowbook is a visual, flow-based notebook for the Genia language.

Users do not primarily write text code.  
They construct programs as **composable flow graphs**.

## Core Principles

1. Flow-first, not UI-first
- Every visual element represents a Genia runtime concept
- UI is a projection of the execution model, not the source of truth

2. Pipelines are the primary abstraction
- Everything should compose via flow pipelines
- Avoid introducing non-composable control structures

3. Value vs Flow must remain explicit
- Do not blur or auto-convert between them implicitly
- Respect Genia semantics

4. Option/none handling is explicit
- Do not silently drop or coerce values
- Support branching / dead-letter flows instead of hidden behavior

5. Single source of truth = graph model
- The graph structure defines execution
- UI state must derive from the graph, not duplicate it

## Architecture Guidelines

- Separate:
  - Graph model (pure data)
  - Execution engine
  - UI rendering layer

- Prefer:
  - Immutable data structures
  - Pure transformations
  - Declarative rendering

- Avoid:
  - UI-driven logic
  - Hidden side effects
  - Implicit state mutation

## Code Generation Rules

When generating code:
- Always model flows explicitly
- Prefer small composable units
- Do not introduce abstractions that cannot map to Genia

If unsure:
→ Choose correctness of the flow model over UI convenience
