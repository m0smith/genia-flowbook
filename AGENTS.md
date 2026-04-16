# AGENTS.md

Genia Flowbook – Copilot Instructions

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


## Purpose

This document defines how AI agents (Codex, ChatGPT, Copilot, and similar tools) must operate within this repository.

The goals are:

- preserve project philosophy
- ensure implementation and documentation never drift
- keep changes minimal, correct, and reviewable
- enforce a truthful, test-backed workflow

---

## Source of Truth

Agents **must treat the following as authoritative and synchronized**:

- `PROJECT_STATE.md` → what is actually implemented now (ground truth)
- `PROJECT_RULES.md` → semantics, invariants, and constraints
- `README.md` → high-level overview
- `docs/book/*` → deeper explanations that must reflect reality
- `docs/cheatsheet/*` → quick reference for implemented behavior only
- `docs/interop/*` → host / environment / external-system contracts when relevant
- `docs/architecture/*` → internal structure decisions when relevant
- `docs/ai/LLM_CONTRACT.md` → shared cross-tool AI guidance

If these disagree, **`PROJECT_STATE.md` is the final authority**.

---

## Non-Negotiable Rule (CRITICAL)

Any change to behavior, syntax, runtime semantics, parser rules, public API shape, or examples MUST also update:

- `PROJECT_STATE.md`
- relevant docs under `docs/book/`
- relevant cheatsheets under `docs/cheatsheet/` when user-facing behavior or examples change

Documentation must describe **only behavior that is implemented and verified by tests**.

No exceptions.

---

## Core Philosophy

1. Preserve simplicity
   - prefer minimal solutions
   - avoid cleverness over clarity
   - avoid hidden behavior

2. Keep semantics explicit
   - no surprising fallbacks
   - no undocumented magic
   - no speculative features presented as real

3. Keep docs truthful
   - docs are not marketing
   - docs are not future plans
   - docs must match implementation

4. Keep the host boundary small
   - host/platform-specific code should remain narrow
   - public behavior should stay as portable as possible

5. Prefer small, focused changes
   - one feature at a time
   - one kind of thinking at a time
   - avoid mixing design, implementation, test, and docs in a single prompt when possible

---

## Required Workflow for Any Meaningful Change

Step 1: Read first
- `PROJECT_STATE.md`
- `PROJECT_RULES.md`
- relevant docs in `docs/book/`
- relevant docs in `docs/interop/` or `docs/architecture/` if the change touches those areas

Step 2: Run pre-flight
- fill out the pre-flight checklist before implementation for non-trivial changes

Step 3: Use the prompt pipeline
- Spec
- Design
- Implementation
- Test
- Docs
- Audit

Step 4: Validate truthfulness
- docs match implementation
- examples are valid
- tests cover the claimed behavior
- no broader claims than what is actually implemented

---

## Prompt Discipline

Every prompt should be narrow in responsibility.

Do not combine too many of these in one prompt:
- architecture decisions
- design
- implementation
- testing
- documentation
- refactoring

Default rule:
> Do not introduce behavior not explicitly defined in the spec.

---

## Testing Expectations

Agents must:
- add or update tests for changed behavior
- cover edge cases and failure cases
- preserve existing behavior outside the approved scope
- prefer black-box tests where practical

---

## Anti-Patterns (Forbidden)

- documenting unimplemented behavior
- expanding scope during implementation
- weakening tests just to pass
- “helpful” redesigns not requested in the spec
- contradictory docs across files

---

## Final Rule

If unsure:
choose the simplest solution that matches the spec, preserves current behavior, and keeps the docs truthful.
