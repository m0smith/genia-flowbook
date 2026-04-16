# Flowbook Prompt Guardrails (Genia-First Enforcement)

## Purpose
Prevent host-language drift (Python-first implementations) and ensure Flowbook is built as a **Genia-native system**.

---

## Core Principle

**Flowbook is defined in Genia. Python is only a temporary host shell.**

If Python defines behavior, we have failed.

---

## Non-Negotiable Rules

1. The following MUST be defined in Genia terms:
   - Notebook model
   - Cell model
   - Pipeline/value semantics
   - Execution behavior
   - Save/load format

2. Python (or any host) may ONLY:
   - Render UI
   - Handle platform integration
   - Bootstrap execution
   - Provide temporary adapters

3. Python MUST NOT:
   - Define notebook meaning
   - Be the source of truth
   - Contain the canonical data model
   - Replace missing Genia features silently

---

## Required Design Pattern

Every change must explicitly separate:

### 1. Portable Genia Contract
- Language-level meaning
- Data structures
- Execution semantics

### 2. Host Adapter (Python)
- Rendering
- IO
- Wiring
- Temporary bridging only

### 3. Not Yet Implemented
- Missing Genia capabilities
- Explicitly called out (never hidden in Python)

---

## Red Flags (Immediate Stop Conditions)

If ANY of these appear, STOP and redesign:

- Python classes defining notebook/cell structure
- Business logic living in Python instead of Genia
- “We’ll just do this in Python for now” without documenting the gap
- Inability to swap Python for another host without changing behavior
- Notebook format only exists as Python objects

---

## Required Prompt Add-On

Every Copilot prompt MUST include:


GENIA FLOWBOOK IMPLEMENTATION RULES

This project is Genia-first, not Python-first.

Non-negotiable rules:

Genia owns semantics.
Python is only a thin adapter.
Do not define notebook behavior in Python.
If Genia cannot express something, name the gap.
Do not silently implement semantics in Python.

---

## Audit Question (Always Ask)

> “If we deleted all Python code, would Flowbook still have a valid definition?”

- If NO → you are building a Python app
- If YES → you are building Genia

---

## Success Criteria

Flowbook is successful when:

- Notebook format is portable and language-defined
- Multiple hosts (Python, JS, etc.) could render it
- Behavior is identical across hosts
- Genia owns all meaning

---

## Mental Model

❌ WRONG: “A Python notebook app for Genia”  
✅ RIGHT: “A Genia notebook with a Python viewer”

---

## Final Reminder

> The host is scaffolding. Genia is the building.