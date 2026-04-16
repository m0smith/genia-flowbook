import type { NotebookData } from './types';
import type { FlowGraph } from '../model/types';

export const PROTOTYPE_PIPELINE_CELL_ID = 'main-pipeline';

// This adapter is temporary host scaffolding. It keeps the current graph editor
// usable while routing execution through notebook-shaped Flowbook core data.
export function prototypeGraphToNotebook(graph: FlowGraph): NotebookData {
  return {
    version: '1.0.0',
    metadata: {
      source: 'temporary-react-host',
      description: 'Prototype graph wrapped as a single pipeline_cell',
    },
    cells: [
      {
        id: PROTOTYPE_PIPELINE_CELL_ID,
        type: 'pipeline_cell',
        pipeline: {
          nodes: graph.nodes.map((node) => ({
            id: node.id,
            type: node.type,
            operation: node.operation,
            x: node.x,
            y: node.y,
          })),
          edges: graph.edges.map((edge) => ({
            id: edge.id,
            from: edge.from,
            to: edge.to,
          })),
        },
      },
    ],
  };
}

