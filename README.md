# Genia Flowbook

A visual, flow-based notebook for the **Genia** programming language. Programs are represented as composable flow graphs — not text.

## Tech Stack

- **Vite + React + TypeScript**
- No heavy diagram frameworks — pure SVG rendering
- Clean separation of model, execution, and UI

## Project Structure

```
src/
  model/       # FlowNode, FlowEdge, FlowGraph types + factory helpers
  engine/      # Operations map + topological graph executor
  ui/          # SVG canvas, node/edge views, toolbar
  App.tsx      # State wiring
```

## Getting Started

```bash
npm install
npm run dev     # start dev server
npm run build   # production build
npm test        # run Vitest tests
```

## Default Pipeline

The app loads a default pipeline: `source → lines → map(parse_int) → sum`  
Click **Run Pipeline** to execute it and see `[15]` as the final output.

## Interacting with the Canvas

- **Click a node** to select it
- **Add Node** buttons add a new node and let you connect it to an existing node
- **Run Pipeline** executes the graph and shows per-node intermediate outputs
- **Reset** restores the default pipeline
