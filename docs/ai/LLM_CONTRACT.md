# LLM Contract

This file contains shared cross-tool AI guidance.

It exists to keep different AI tools aligned without redefining the project's actual semantics.

## Rules

- Read `PROJECT_STATE.md`, `PROJECT_RULES.md`, and `AGENTS.md` first.
- Treat `PROJECT_STATE.md` as final authority.
- Do not invent behavior not defined in spec.
- Keep prompts narrow and role-specific.
- Keep documentation truthful and synchronized.

## Role separation

- Spec prompts define truth
- Design prompts define structure
- Implementation prompts build only approved behavior
- Test prompts verify
- Docs prompts synchronize reality
- Audit prompts challenge everything skeptically
