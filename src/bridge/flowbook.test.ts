import { describe, expect, it } from 'vitest';
import { executeNotebook, validateNotebook } from './flowbook';
import { PROTOTYPE_PIPELINE_CELL_ID, prototypeGraphToNotebook } from './adapters';
import { createEdge, createGraph, createNode } from '../model';
import type { NotebookData, PipelineCellData } from './types';

function makeDefaultGraph() {
  return createGraph(
    [
      createNode('n1', 'source', 'input', 100, 200),
      createNode('n2', 'transform', 'inc', 300, 200),
      createNode('n3', 'sink', 'sum', 500, 200),
    ],
    [
      createEdge('n1', 'n2'),
      createEdge('n2', 'n3'),
    ],
  );
}

function mainPipelineCell(notebook: NotebookData): PipelineCellData {
  return notebook.cells[0] as PipelineCellData;
}

describe('Flowbook bridge contract', () => {
  it('accepts notebook-shaped input and returns Genia-owned execution results', () => {
    const notebook = prototypeGraphToNotebook(makeDefaultGraph());

    const result = executeNotebook({ notebook });

    expect(result).toMatchObject({
      status: 'success',
      notebook_valid: true,
      execution_order: [PROTOTYPE_PIPELINE_CELL_ID],
      bindings: {},
    });
    expect(result.error).toBeNull();
    expect(result.cell_results[PROTOTYPE_PIPELINE_CELL_ID]).toMatchObject({
      status: 'success',
      output: [0],
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
