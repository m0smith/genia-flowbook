# Prompt 6 — Audit / Truth Review

You are working on this project.

Before doing anything, read completely:

Authoritative:
- `AGENTS.md`
- `PROJECT_STATE.md` (FINAL AUTHORITY)
- `PROJECT_RULES.md`
- `README.md`

Relevant (only those touched):
- `docs/book/*`
- `docs/cheatsheet/*`
- `docs/interop/*`
- `docs/architecture/*`
- `tests/*`
- implementation files changed

Pipeline artifacts:
- pre-flight
- spec output
- design output
- implementation changes
- test changes
- documentation updates

## Task type: AUDIT ONLY

Audit the completed feature.

You are NOT implementing anything.

## Primary mindset (critical)
Assume the implementation is WRONG until proven correct.

Your job is to find:
- mismatches
- drift
- lies in docs
- hidden behavior
- unnecessary complexity

## Scope lock
You must NOT:
- redesign the feature
- expand scope
- introduce new behavior
- suggest speculative improvements

If a fix requires redesign:
mark as FAIL and stop at recommendations.

## Required checks
1. Spec ↔ implementation
2. Design ↔ implementation
3. Test validity
4. Regression check
5. Truthfulness (docs)
6. Cross-file consistency
7. Host/platform/capability boundary discipline if relevant
8. Complexity audit
9. Ordered minimal fixes

## Output format
Return exactly:
1. Status (PASS / PASS WITH ISSUES / FAIL)
2. Summary
3. Spec mismatches
4. Design mismatches
5. Test gaps
6. Regression issues
7. Documentation issues
8. Cross-file inconsistencies
9. Complexity assessment
10. Issue list
11. Recommended fixes
12. Final verdict (Ready to merge: YES / NO)

## Final rule
If something is unclear, undocumented, or exceeds scope, treat it as incorrect.
