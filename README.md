# Genia Flowbook

Flowbook is a visual, flow-based notebook for the **Genia** language.

The product direction is:
- **Genia owns notebook and pipeline semantics**
- **the current React app is a temporary host shell**

This repository is in a staged migration from an early graph prototype to a real notebook core.

## Current Status

What is true today:
- The browser app renders and edits a graph-shaped demo.
- That demo now routes through a notebook-shaped Flowbook core boundary in TypeScript.
- In Node/test environments, that TypeScript boundary delegates validation and execution into the Genia-owned Python path.
- The current browser path no longer executes pipelines in TypeScript and still fails closed until browser/runtime transport is wired to Genia.
- `src/genia/flowbook` now includes an in-repo Genia-owned workflow runner for minimal pipeline execution and validation.
- The React app is **not** the semantic source of truth anymore.

What is **not** true today:
- Browser-native Genia is not implemented.
- A real Genia runtime transport between the React host and `src/genia/flowbook` is not implemented.
- Full notebook execution for all five notebook cell types is not implemented in the active host path.

If you need the final authority on implemented state, read [PROJECT_STATE.md](/Users/m0smith/projects/genia-flowbook/PROJECT_STATE.md).

## Direction

Flowbook semantics belong in Genia, not in the host shell.

The authoritative design and conversion docs are:
- [docs/book/NOTEBOOK_SPEC.md](/Users/m0smith/projects/genia-flowbook/docs/book/NOTEBOOK_SPEC.md)
- [docs/architecture/CORE_ARCHITECTURE.md](/Users/m0smith/projects/genia-flowbook/docs/architecture/CORE_ARCHITECTURE.md)
- [docs/conversion/GENIA_CORE_CONVERSION_SPEC.md](/Users/m0smith/projects/genia-flowbook/docs/conversion/GENIA_CORE_CONVERSION_SPEC.md)
- [docs/conversion/GENIA_CORE_CONVERSION_DESIGN.md](/Users/m0smith/projects/genia-flowbook/docs/conversion/GENIA_CORE_CONVERSION_DESIGN.md)

The current React app exists to:
- render and edit temporary host data
- send notebook-shaped requests through the host bridge
- display returned execution results

It must not define notebook semantics, pipeline semantics, or operation semantics.

## Repository Shape

```text
src/
  core/flowbook/   # Thin host transport/client boundary; not the semantic runtime
  bridge/          # Host bridge + temporary graph-to-notebook adapter
  model/           # Temporary graph editor data for the React host
  engine/          # Deprecated compatibility wrapper; not authoritative
  ui/              # SVG host-shell UI
  App.tsx          # Temporary host shell wiring

src/genia/flowbook/
  # Genia-owned notebook core path, including the local workflow runner MVP
```

Important:
- `src/core/flowbook` is a thin host boundary and must not define notebook or pipeline semantics.
- `src/engine` is compatibility scaffolding and must not regain semantic ownership.
- `src/genia/flowbook` is the intended long-term home of Flowbook core semantics.

## Running The Demo

```bash
npm install
npm run dev
npm run build
npm test
```

The default demo still renders the prototype pipeline:

`input -> inc -> sum`

In Node/test environments, the host boundary now delegates to the Genia-owned Python path. In the browser, execution still fails with a structured runtime error until a real browser/runtime transport is wired in.

Inside `src/genia/flowbook`, the current local Genia-owned workflow MVP supports the operations:

- `input`
- `inc`
- `map`
- `sum`

## What To Build Next

The next implementation milestone is **not** UI polish.

The next implementation milestone is:
1. notebook cells as first-class data
2. notebook execution across cells
3. wiring the active host path to the Genia-owned runtime path that now exists in-repo

If a choice comes up between UI convenience and semantic correctness, choose semantic correctness.

## Contributor Rule

Do not add new product semantics to the React host, `src/model`, or `src/engine`.

If you need to change:
- notebook structure
- execution ordering
- operation meaning
- cell behavior
- result/error semantics

then that change belongs in the Flowbook core direction defined by the conversion and architecture docs, not in host-only code.
