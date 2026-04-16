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
            { id: 'n1', type: 'source', operation: 'source', x: 100, y: 200 },
            { id: 'n2', type: 'transform', operation: 'lines', x: 300, y: 200 },
            { id: 'n3', type: 'transform', operation: 'map(parse_int)', x: 500, y: 200 },
            { id: 'n4', type: 'sink', operation: 'sum', x: 700, y: 200 },
          ],
          edges: [
            { id: 'n1->n2', from: 'n1', to: 'n2' },
            { id: 'n2->n3', from: 'n2', to: 'n3' },
            { id: 'n3->n4', from: 'n3', to: 'n4' },
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
  it('fails safely when no Genia runtime adapter is wired into the host path', () => {
    const result = executeNotebook(makeDefaultNotebook());

    expect(result.status).toBe('error');
    expect(result.notebook_valid).toBe(true);
    expect(result.execution_order).toEqual(['main-pipeline']);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'EXECUTION_FAILED',
      location: {
        step: 'execution',
        context: 'Pipeline execution',
      },
    });

    const pipelineResult = result.cell_results['main-pipeline'];
    expect(pipelineResult.status).toBe('error');
    if (pipelineResult.status === 'error') {
      expect(pipelineResult.error).toMatchObject({
        code: 'EXECUTION_FAILED',
        message:
          'Flowbook execution requires a Genia runtime adapter; host-side pipeline execution is disabled.',
      });
    }
  });

  it('returns a structured unknown-operation error through the core contract', () => {
    const notebook = makeDefaultNotebook();
    mainPipelineCell(notebook).pipeline.nodes[0].operation = 'nonexistent';

    const result = executeNotebook(notebook);

    expect(result.status).toBe('error');
    expect(result.notebook_valid).toBe(false);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'UNKNOWN_OPERATION',
      location: {
        step: 'validation',
        context: "pipeline_cell 'main-pipeline'",
      },
      cell_id: 'main-pipeline',
    });
    expect(result.error?.details).toMatchObject({
      operation: 'nonexistent',
    });
  });

  it('returns a structured execution failure instead of host-side cycle execution', () => {
    const notebook = makeDefaultNotebook();
    mainPipelineCell(notebook).pipeline.edges.push({ id: 'n4->n1', from: 'n4', to: 'n1' });

    const result = executeNotebook(notebook);

    expect(result.status).toBe('error');
    expect(result.notebook_valid).toBe(true);
    expect(result.error).toMatchObject({
      type: 'error',
      code: 'EXECUTION_FAILED',
      location: {
        step: 'execution',
        context: 'Pipeline execution',
      },
    });
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
        context: "pipeline_cell 'main-pipeline'",
      },
      cell_id: 'main-pipeline',
    });
    expect(result.error?.details).toEqual({
      edge_id: 'n1->missing',
      from: 'n1',
      to: 'missing',
    });
  });

  it('round-trips notebook data through JSON serialization without changing failure semantics', () => {
    const notebook = makeDefaultNotebook();
    const serialized = JSON.stringify(notebook);
    const parsed = JSON.parse(serialized) as NotebookData;

    expect(validateNotebook(parsed)).toEqual({ ok: true, notebook_valid: true });

    const result = executeNotebook(parsed);
    expect(result.status).toBe('error');

    const pipelineResult = result.cell_results['main-pipeline'];
    expect(pipelineResult.status).toBe('error');
    if (pipelineResult.status === 'error') {
      expect(pipelineResult.error.code).toBe('EXECUTION_FAILED');
    }
  });
});
