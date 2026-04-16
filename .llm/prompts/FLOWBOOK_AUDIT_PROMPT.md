# Flowbook Audit Prompt (Post-Implementation)

Use this after every major Copilot run.

---

## Prompt

Audit the current Flowbook implementation for host-language semantic drift.

GENIA FLOWBOOK IMPLEMENTATION RULES

This project is Genia-first, not Python-first.

Non-negotiable rules:
- Genia owns semantics
- Python is only an adapter
- No notebook meaning in Python

---

## Audit For:

1. Python defining notebook/cell structure
2. Python-only representations of core concepts
3. Missing separation between contract and adapter
4. Overly “smart” Python logic
5. Inability to swap hosts without behavior change

---

## Output Format

For each issue:

- Severity: HIGH / MEDIUM / LOW
- File(s):
- Problem:
- Why it violates Genia-first:
- Recommended fix:

---

## Final Verdict

- Is Flowbook still Genia-first? YES / NO
- Top 3 fixes required immediately: