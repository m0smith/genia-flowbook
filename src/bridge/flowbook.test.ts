import { describe, expect, it } from 'vitest';
import { executeNotebook, validateNotebook } from './flowbook';
import { PROTOTYPE_PIPELINE_CELL_ID, prototypeGraphToNotebook } from './adapters';
import { createEdge, createGraph, createNode } from '../model';
import type { NotebookData, PipelineCellData } from './types';

function makeDefaultGraph() {
  return createGraph(
    [
      createNode('n1', 'source', 'source', 100, 200),
      createNode('n2', 'transform', 'lines', 300, 200),
      createNode('n3', 'transform', 'map(parse_int)', 500, 200),
      createNode('n4', 'sink', 'sum', 700, 200),
    ],
    [
      createEdge('n1', 'n2'),
      createEdge('n2', 'n3'),
      createEdge('n3', 'n4'),
    ],
  );
}

function mainPipelineCell(notebook: NotebookData): PipelineCellData {
  return notebook.cells[0] as PipelineCellData;
}

describe('Flowbook bridge contract', () => {
  it('accepts notebook-shaped input and returns a stable execution failure envelope without Genia', () => {
    const notebook = prototypeGraphToNotebook(makeDefaultGraph());

    const result = executeNotebook({ notebook });

    expect(result).toMatchObject({
      status: 'error',
      notebook_valid: true,
      execution_order: [PROTOTYPE_PIPELINE_CELL_ID],
      bindings: {},
    });
    expect(result.cell_results[PROTOTYPE_PIPELINE_CELL_ID]).toBeDefined();
    expect(result.error).toMatchObject({
      code: 'EXECUTION_FAILED',
    });
  });

  it('validates notebook-shaped input without requiring any UI component state', () => {
    const notebook = prototypeGraphToNotebook(makeDefaultGraph());

    const result = validateNotebook({ notebook });

    expect(result).toEqual({
      ok: true,
      notebook_valid: true,
    });
  });

  it('preserves structured reference errors at the bridge boundary', () => {
    const notebook = prototypeGraphToNotebook(makeDefaultGraph());
    mainPipelineCell(notebook).pipeline.edges.push({
      id: 'missing->n4',
      from: 'missing',
      to: 'n4',
    });

    const result = validateNotebook({ notebook });

    expect(result.ok).toBe(false);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'INVALID_SCHEMA',
      cell_id: PROTOTYPE_PIPELINE_CELL_ID,
    });
  });
});
