# Architecture & Specification Overview

This document summarizes the Flowbook Notebook Core specification and architecture design, and explains how they relate.

---

## Document Map

### 1. Specification
**File**: `docs/book/NOTEBOOK_SPEC.md`  
**Describes**: What the Flowbook Notebook Core must do  
**Audience**: Users, designers, auditors

**Sections**:
- Notebook structure and validation rules
- Five cell types and their schemas
- Pipeline model and data flow
- Reference system (cell IDs, binding names)
- Execution model (order, re-execution, error isolation)
- Error model (structured format)
- Serialization format (JSON)
- Core invariants (9 properties that must always hold)

**Key point**: The spec defines the contract. Any implementation must satisfy it exactly.

---

### 2. Worked Examples
**File**: `docs/book/NOTEBOOK_EXAMPLES.md`  
**Describes**: Valid notebooks, error cases, execution traces  
**Audience**: Users, implementers, testers

**Sections**:
- 6 worked examples showing different notebook patterns
- Execution traces for each example
- Error cases and validation failures
- Conformance checklist

**Key point**: If a notebook conforms to these examples, it conforms to the spec.

---

### 3. Execution Model Explanation
**File**: `docs/architecture/CELLS_AND_EXECUTION.md`  
**Describes**: How the notebook spec relates to existing FlowGraph model  
**Audience**: Implementers, integrators

**Sections**:
- Cell types and their roles
- Relationship to FlowGraph (spec structure + existing executor)
- Full execution flow (parse → validate → execute)
- Execution context (state tracking)
- Error handling and propagation
- Determinism guarantees
- Composability patterns

**Key point**: The notebook orchestrates cell execution; each pipeline_cell contains a FlowGraph that delegates to the Genia interpreter.

---

### 4. Internal Architecture Design
**File**: `docs/architecture/CORE_ARCHITECTURE.md`  
**Describes**: How to build the runtime that implements the spec  
**Audience**: Implementers, architects

**Sections**:
1. **Design summary**: Vision, principles, scope
2. **Core structures**: Data structures for Notebook, Cell types, Pipeline, ExecutionContext, DependencyGraph, StructuredError, Reference
3. **Module layout**: Proposed package structure with responsibilities
4. **Execution architecture**: Full notebook execution, single-cell, error handling, caching strategy
5. **Dependency/reference design**: Building DAGs, validation, acyclicity
6. **Error design**: Classification, construction, reporting
7. **Serialization path**: 3-layer model (Genia data → Spec → Model → Results)
8. **Runtime integration**: What Flowbook owns vs what Genia owns
9. **MVP boundaries**: What's in v1, what defers
10. **Risks**: Potential drift points and mitigations

**Key point**: This design is implementable in any host (JS, Python) without changing fundamentals.

---

## Reading Path

### For implementers
1. Read `PROJECT_RULES.md` (invariants)
2. Read `docs/book/NOTEBOOK_SPEC.md` sections 1–7 (spec contract)
3. Read `docs/architecture/CORE_ARCHITECTURE.md` sections 1–5 (your domain)
4. Implement your part of the design
5. Read `docs/architecture/CORE_ARCHITECTURE.md` sections 6–10 (context on risks, integration)

### For reviewers/auditors
1. Read `PROJECT_RULES.md` (claims about the system)
2. Read `docs/book/NOTEBOOK_SPEC.md` (spec contract)
3. Read test cases (implementation should pass all spec examples)
4. Spot-check `docs/architecture/CORE_ARCHITECTURE.md` for design alignment

### For users/designers
1. Read `README.md` (high-level overview)
2. Read `docs/book/NOTEBOOK_EXAMPLES.md` (what notebooks look like)
3. Read `docs/book/NOTEBOOK_SPEC.md` section 2 (cell types)

---

## Design Principles

### From AGENTS.md (Flowbook philosophy)
1. **Flow-first, not UI-first**: Every element represents a Genia runtime concept
2. **Pipelines are primary**: Everything composes via pipelines
3. **Explicit value vs flow**: No blurring, no auto-conversion
4. **Option/none handling explicit**: No silently dropping values
5. **Single source of truth**: Graph model defines execution

### Applied in specification
- Notebook is an **ordered list of cells** (flow-based, not interaction-based)
- Composition happens via **pipelines** and **bindings**, not UI affordances
- Cell references are **explicit** (no implicit dependencies)
- Errors are **structured** (no silent failures or coerced types)

### Applied in architecture
- **Immutable spec**, mutable execution context (separation of concerns)
- **Three-layer serialization** (data → spec → model) maintains truth
- **Delegation to Genia** (Flowbook orchestrates, interpreter executes)
- **Explicit module boundaries** (no hidden state sharing)

---

## Spec → Design Mapping

### How the spec maps to architecture

| Spec concept | Design structure | Module |
|---|---|---|
| Notebook | `NotebookSpec` | `spec/types.ts` |
| Cell (union of 5 types) | `CellBase + type variants` | `spec/types.ts` |
| pipeline_cell | `PipelineCellSpec` | `spec/types.ts` |
| Pipeline (nodes + edges) | `Pipeline` | `spec/types.ts` |
| Cell ID reference | `Reference` (type="cell_id") | `model/reference.ts` |
| Binding name reference | `Reference` (type="binding_name") | `model/reference.ts` |
| Execution order | `DependencyGraph.topologicalOrder` | `model/dependency.ts` |
| Cell output | `CellResult.output` | `engine/context.ts` |
| Binding | `ExecutionContext.bindings` | `engine/context.ts` |
| Structured error | `StructuredError` | `errors/structured-error.ts` |
| Execution context | `ExecutionContext` | `engine/context.ts` |
| Serialization | `serialize/deserialize` functions | `serialization/*.ts` |

### No spec concepts were invented
Every piece of the architecture directly implements the spec. Nothing extra.

---

## Alignment with Project Rules

### Explicit behavior beats implicit
✅ All state in ExecutionContext is visible  
✅ All references are explicit (cell_id or binding_name)  
✅ All errors are structured and reported  
✅ No hidden caching or optimization in MVP

### Error cases must be specified, not inferred
✅ All error codes are enumerated in spec section 6  
✅ Error design document classifies errors by phase (parse, validate, execute)  
✅ Error construction uses documented factory functions

### Keep semantics explicit
✅ Notebook execution order is deterministic (topological sort)  
✅ Cell output is always in an array (Genia convention)  
✅ Binding scope is explicit (ExecutionContext)  
✅ No implicit type coercion (delegate to Genia)

### Backward compatibility is explicit
✅ Spec includes `version` field for future changes  
✅ MVP scope is clearly defined (no unplanned extensions)  
✅ Risk document identifies potential drift points

---

## Implementation Checklist

Once implementation begins, verify against:

#### Spec compliance
- [ ] Notebook parsing matches spec section 1.1–1.3
- [ ] All 5 cell types implemented per section 2.2
- [ ] Execution model matches section 5.1–5.4
- [ ] Error codes match section 6.2
- [ ] Serialization is JSON per section 7.1–7.3

#### Architecture compliance
- [ ] Core structures match section 2 of architecture design
- [ ] Module boundaries follow section 3 layout
- [ ] Execution engine implements section 4 architecture
- [ ] Dependency graph enforces section 5 rules
- [ ] Errors use design from section 6
- [ ] Serialization follows section 7 path
- [ ] Genia integration matches section 8
- [ ] MVP scope matches section 9

#### Quality
- [ ] No circular module dependencies
- [ ] All test cases from NOTEBOOK_EXAMPLES.md pass
- [ ] Error messages include structure for UI
- [ ] Execution is deterministic (same input → same order)
- [ ] No host-specific code in core modules

---

## Open Design Questions

These are design decisions that remain flexible:

1. **Fail-fast vs fail-through execution?**
   - Spec allows either; design recommends fail-fast for MVP
   - Implementation choice; can change in future

2. **Multiple sinks in a pipeline?**
   - Spec says "return final node output"
   - What if there are multiple terminals?
   - Design: return last-executed node (per topological order)
   - Could change in future with richer output model

3. **Binding scope lifetime?**
   - Design: bindings exist for duration of notebook execution
   - Question: Are they persistent across executions?
   - Answer: Results are separate from notebook (section 7.5); not persistent by default

4. **Operation parameter resolution?**
   - Spec: operation names like `"map(parse_int)"` are atomic
   - Design: future extension could add parameter binding
   - Not in MVP; deferred per section 9.2

5. **Partial recomputation strategy?**
   - Design: Deferred until caching is needed
   - Question: Which cells to recompute on a change?
   - Answer: Will require invalidation DAG; not MVP

---

## Summary

The specification and architecture work together:

- **Spec** defines WHAT (contract and semantics)
- **Architecture** defines HOW (structure and modules)
- **Examples** demonstrate BOTH (concrete notebooks)
- **Rules** enforce quality (invariants and principles)

Together, they form a complete, portable, and explicit design for the Flowbook Notebook Core.

---

**End of Overview**
