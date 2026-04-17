import { describe, expect, it } from 'vitest';
import { executeNotebook, validateNotebook } from './api';
import type { NotebookData, PipelineCellData } from './types';

function makeDefaultNotebook(): NotebookData {
  return {
    version: '1.0.0',
    cells: [
      {
        id: 'main-pipeline',
        type: 'pipeline_cell',
        pipeline: {
          nodes: [
            { id: 'n1', type: 'source', operation: 'input', x: 100, y: 200 },
            { id: 'n2', type: 'transform', operation: 'inc', x: 300, y: 200 },
            { id: 'n3', type: 'sink', operation: 'sum', x: 500, y: 200 },
          ],
          edges: [
            { id: 'n1->n2', from: 'n1', to: 'n2' },
            { id: 'n2->n3', from: 'n2', to: 'n3' },
          ],
        },
      },
    ],
  };
}

function mainPipelineCell(notebook: NotebookData): PipelineCellData {
  return notebook.cells[0] as PipelineCellData;
}

describe('Flowbook core execution', () => {
  it('delegates execution to the Genia-owned runtime path', () => {
    const result = executeNotebook(makeDefaultNotebook());

    expect(result.status).toBe('success');
    expect(result.notebook_valid).toBe(true);
    expect(result.execution_order).toEqual(['main-pipeline']);
    expect(result.error).toBeNull();

    const pipelineResult = result.cell_results['main-pipeline'];
    expect(pipelineResult.status).toBe('success');
    if (pipelineResult.status === 'success') {
      expect(pipelineResult.output).toEqual([0]);
      expect(pipelineResult.node_outputs).toEqual({
        n1: [],
        n2: [],
        n3: [0],
      });
    }
  });

  it('returns a structured unknown-operation execution error from the Genia-owned contract', () => {
    const notebook = makeDefaultNotebook();
    mainPipelineCell(notebook).pipeline.nodes[0].operation = 'nonexistent';

    const result = executeNotebook(notebook);

    expect(result.status).toBe('error');
    expect(result.notebook_valid).toBe(true);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'EXECUTION_FAILED',
      cell_id: 'main-pipeline',
    });
    expect(result.error?.message).toContain("Unknown operation 'nonexistent'.");
  });

  it('returns a structured cycle execution error from the Genia-owned runtime', () => {
    const notebook = makeDefaultNotebook();
    mainPipelineCell(notebook).pipeline.edges.push({ id: 'n3->n1', from: 'n3', to: 'n1' });

    const result = executeNotebook(notebook);

    expect(result.status).toBe('error');
    expect(result.notebook_valid).toBe(true);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'EXECUTION_FAILED',
      cell_id: 'main-pipeline',
    });
    expect(result.error?.message).toContain('Cycle detected in workflow graph.');
  });

  it('returns a structured malformed-edge error through validation', () => {
    const notebook = makeDefaultNotebook();
    mainPipelineCell(notebook).pipeline.edges[0] = {
      id: 'n1->missing',
      from: 'n1',
      to: 'missing',
    };

    const result = validateNotebook(notebook);

    expect(result.ok).toBe(false);
    expect(result.notebook_valid).toBe(false);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'INVALID_SCHEMA',
      location: {
        step: 'validation',
        context: 'Schema validation',
      },
      cell_id: 'main-pipeline',
    });
    expect(result.error?.details).toEqual({});
  });

  it('round-trips notebook data through JSON serialization without changing failure semantics', () => {
    const notebook = makeDefaultNotebook();
    const serialized = JSON.stringify(notebook);
    const parsed = JSON.parse(serialized) as NotebookData;

    expect(validateNotebook(parsed)).toEqual({ ok: true, notebook_valid: true });

    const result = executeNotebook(parsed);
    expect(result.status).toBe('success');

    const pipelineResult = result.cell_results['main-pipeline'];
    expect(pipelineResult.status).toBe('success');
    if (pipelineResult.status === 'success') {
      expect(pipelineResult.output).toEqual([0]);
    }
  });
});
