# Genia Flowbook

Flowbook is a visual, flow-based notebook for the **Genia** language.

The product direction is:
- **Genia owns notebook and pipeline semantics**
- **the current React app is a temporary host shell**

This repository is in a staged migration from an early graph prototype to a real notebook core.

## Current Status

What is true today:
- The browser app renders and edits a graph-shaped demo.
- That demo now executes through a notebook-shaped Flowbook core boundary in TypeScript.
- The current browser path uses a **temporary compatibility runtime** to preserve the demo behavior.
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
  core/flowbook/   # Current Flowbook execution boundary for the host path
  bridge/          # Host bridge + temporary graph-to-notebook adapter
  model/           # Temporary graph editor data for the React host
  engine/          # Deprecated compatibility wrapper; not authoritative
  ui/              # SVG host-shell UI
  App.tsx          # Temporary host shell wiring

src/genia/flowbook/
  # Target Genia-owned notebook core path
```

Important:
- `src/core/flowbook` is the current executable boundary for the browser demo path.
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

`source -> lines -> map(parse_int) -> sum`

Running it should still produce `[15]`.

That preserved output is a compatibility goal for the host demo. It does **not** mean the graph prototype is the final Flowbook model.

## What To Build Next

The next implementation milestone is **not** UI polish.

The next implementation milestone is:
1. notebook cells as first-class data
2. notebook execution across cells
3. replacement of the temporary compatibility runtime with a real Genia-owned runtime path

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
