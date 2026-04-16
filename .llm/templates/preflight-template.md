=== PROJECT PRE-FLIGHT ===

CHANGE NAME:
<short name of change>

--------------------------------
1. SCOPE LOCK
--------------------------------

Change includes:
-
-

Change does NOT include:
-
-

--------------------------------
2. SOURCE OF TRUTH
--------------------------------

Authoritative files:
- PROJECT_STATE.md (final authority)
- PROJECT_RULES.md
- README.md
- AGENTS.md

Additional relevant:
-

Notes:
-

--------------------------------
3. FEATURE MATURITY
--------------------------------

Stage:
[ ] Experimental
[ ] Partial
[ ] Stable

How this must be described in docs:
-

--------------------------------
4. CONTRACT vs IMPLEMENTATION
--------------------------------

Contract (portable semantics):
- 

Implementation (Python today):
- 

Not implemented:
- 

Flowbook ownership check:
- Is the notebook/cell/pipeline model defined in Genia terms? YES / NO
- Is any host language defining Flowbook semantics? YES / NO

If YES:
- STOP and redesign before implementation

- What is the thinnest possible host adapter?
- What missing Genia capability is forcing host support?
- What is the plan to remove or isolate that dependency?

--------------------------------
5. TEST STRATEGY
--------------------------------

Core invariants:
-
-

Expected behaviors:
-
-

Failure cases:
-
-

How this will be tested:
-

--------------------------------
6. EXAMPLES
--------------------------------

Minimal example:
-

Real example (if applicable):
-

--------------------------------
7. COMPLEXITY CHECK
--------------------------------

Is this:
[ ] Adding complexity
[ ] Revealing structure

Justification:
-

--------------------------------
8. CROSS-FILE IMPACT
--------------------------------

Files that must change:
-
-

Risk of drift:
[ ] Low
[ ] Medium
[ ] High

--------------------------------
9. PHILOSOPHY CHECK
--------------------------------

Does this:
- preserve minimalism? YES / NO
- avoid hidden behavior? YES / NO
- keep semantics out of host? YES / NO
- align with pattern-matching-first? YES / NO

Flowbook-specific:
- keeps Flowbook core in Genia rather than host code? YES / NO
- prevents host adapter from becoming the spec? YES / NO

Notes:
-

--------------------------------
10. PROMPT PLAN
--------------------------------

Will use prompt pipeline?
YES / NO

If YES:
- Spec
- Design
- Implementation
- Test
- Docs
- Audit

--------------------------------
FINAL GO / NO-GO
--------------------------------

Ready to proceed?
YES / NO

If NO, what is missing:
-
