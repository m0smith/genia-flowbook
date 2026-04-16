# Prompt Workflow

Use this order for non-trivial changes:

1. Fill out pre-flight (`.llm/templates/preflight-template.md`)
2. Run spec prompt (`.llm/prompts/spec.md`)
3. Run design prompt (`.llm/prompts/design.md`)
4. Run implementation prompt (`.llm/prompts/implement.md`)
5. Run test prompt (`.llm/prompts/test.md`)
6. Run docs prompt (`.llm/prompts/docs.md`)
7. Run audit prompt (`.llm/prompts/audit.md`)

## Core rule

Each prompt should do one kind of thinking only.

## Merge rule

A change is not done until:
- tests pass
- docs are synchronized
- audit result is PASS or PASS WITH ISSUES that are consciously accepted
