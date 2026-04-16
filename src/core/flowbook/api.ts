import {
  type BindingCellData,
  type CellResultData,
  type CellResultSuccessData,
  type GeniaValue,
  type NotebookData,
  type NotebookExecutionResultData,
  type PipelineCellData,
  type StructuredErrorData,
  type ValidateNotebookResult,
} from './types';
import { getDefaultPipelineRuntime, type PipelineRuntime } from './runtime';

function makeError(
  code: StructuredErrorData['code'],
  message: string,
  step: StructuredErrorData['location']['step'],
  context: string,
  cell_id?: string,
  details: Record<string, unknown> = {},
): StructuredErrorData {
  return {
    type: 'error',
    code,
    message,
    location: { step, context },
    cell_id,
    details,
  };
}

function validatePipelineCell(
  cell: PipelineCellData,
  runtime: PipelineRuntime,
): StructuredErrorData | undefined {
  const nodeIds = new Set<string>();
  for (const node of cell.pipeline.nodes) {
    if (nodeIds.has(node.id)) {
      return makeError(
        'INVALID_SCHEMA',
        `Duplicate node ID '${node.id}'`,
        'validation',
        `pipeline_cell '${cell.id}'`,
        cell.id,
      );
    }
    nodeIds.add(node.id);

    if (!runtime.listOperations().includes(node.operation)) {
      return makeError(
        'UNKNOWN_OPERATION',
        `Operation '${node.operation}' is not registered`,
        'validation',
        `pipeline_cell '${cell.id}'`,
        cell.id,
        { operation: node.operation, available_operations: runtime.listOperations() },
      );
    }
  }

  const edgeIds = new Set<string>();
  for (const edge of cell.pipeline.edges) {
    if (edgeIds.has(edge.id)) {
      return makeError(
        'INVALID_SCHEMA',
        `Duplicate edge ID '${edge.id}'`,
        'validation',
        `pipeline_cell '${cell.id}'`,
        cell.id,
      );
    }
    edgeIds.add(edge.id);

    if (!nodeIds.has(edge.from) || !nodeIds.has(edge.to)) {
      return makeError(
        'INVALID_SCHEMA',
        `Edge '${edge.id}' references a missing node`,
        'validation',
        `pipeline_cell '${cell.id}'`,
        cell.id,
        { edge_id: edge.id, from: edge.from, to: edge.to },
      );
    }
  }

  return undefined;
}

export function validateNotebook(
  notebook: NotebookData,
  runtime: PipelineRuntime = getDefaultPipelineRuntime(),
): ValidateNotebookResult {
  if (!notebook || typeof notebook !== 'object') {
    return {
      ok: false,
      notebook_valid: false,
      error: makeError('PARSE_ERROR', 'Notebook must be an object', 'parsing', 'Notebook parsing'),
    };
  }

  if (!Array.isArray(notebook.cells) || notebook.cells.length === 0) {
    return {
      ok: false,
      notebook_valid: false,
      error: makeError(
        'INVALID_SCHEMA',
        'Notebook must contain at least one cell',
        'validation',
        'Notebook validation',
      ),
    };
  }

  const cellIds = new Set<string>();
  const bindingNames = new Set<string>();
  const reservedNames = new Set(runtime.listOperations());

  for (let index = 0; index < notebook.cells.length; index += 1) {
    const cell = notebook.cells[index];

    if (cellIds.has(cell.id)) {
      return {
        ok: false,
        notebook_valid: false,
        error: makeError(
          'DUPLICATE_CELL_ID',
          `Duplicate cell ID '${cell.id}'`,
          'validation',
          'Cell ID uniqueness',
          cell.id,
        ),
      };
    }
    cellIds.add(cell.id);

    if (cell.type === 'note_cell' && !cell.content) {
      return {
        ok: false,
        notebook_valid: false,
        error: makeError(
          'INVALID_SCHEMA',
          `Note cell '${cell.id}' content must be non-empty`,
          'validation',
          'Cell validation',
          cell.id,
        ),
      };
    }

    if (cell.type === 'pipeline_cell') {
      const pipelineError = validatePipelineCell(cell, runtime);
      if (pipelineError) {
        return { ok: false, notebook_valid: false, error: pipelineError };
      }

      for (const depId of cell.depends_on ?? []) {
        const depIndex = notebook.cells.findIndex((candidate) => candidate.id === depId);
        if (depIndex === -1) {
          return {
            ok: false,
            notebook_valid: false,
            error: makeError(
              'MISSING_CELL_REFERENCE',
              `Cell '${cell.id}' references missing cell '${depId}'`,
              'validation',
              'Reference validation',
              cell.id,
              { referenced_cell: depId },
            ),
          };
        }
        if (depIndex >= index) {
          return {
            ok: false,
            notebook_valid: false,
            error: makeError(
              'FORWARD_REFERENCE',
              `Cell '${cell.id}' references cell '${depId}' which appears after it`,
              'validation',
              'Reference ordering',
              cell.id,
              { referenced_cell: depId },
            ),
          };
        }
      }
    }

    if (cell.type === 'inspect_cell' || cell.type === 'binding_cell') {
      const sourceIndex = notebook.cells.findIndex(
        (candidate) => candidate.id === cell.source_cell_id,
      );
      if (sourceIndex === -1) {
        return {
          ok: false,
          notebook_valid: false,
          error: makeError(
            'MISSING_CELL_REFERENCE',
            `Cell '${cell.id}' references missing cell '${cell.source_cell_id}'`,
            'validation',
            'Reference validation',
            cell.id,
            { referenced_cell: cell.source_cell_id },
          ),
        };
      }
      if (sourceIndex >= index) {
        return {
          ok: false,
          notebook_valid: false,
          error: makeError(
            'FORWARD_REFERENCE',
            `Cell '${cell.id}' references cell '${cell.source_cell_id}' which appears after it`,
            'validation',
            'Reference ordering',
            cell.id,
            { referenced_cell: cell.source_cell_id },
          ),
        };
      }
      const source = notebook.cells[sourceIndex];
      if (source.type === 'note_cell') {
        return {
          ok: false,
          notebook_valid: false,
          error: makeError(
            'INVALID_SCHEMA',
            `Cell '${cell.id}' cannot reference non-executable note_cell '${cell.source_cell_id}'`,
            'validation',
            'Reference validation',
            cell.id,
          ),
        };
      }
    }

    if (cell.type === 'binding_cell') {
      if (bindingNames.has(cell.binding_name) || reservedNames.has(cell.binding_name)) {
        return {
          ok: false,
          notebook_valid: false,
          error: makeError(
            'INVALID_BINDING_NAME',
            `Binding name '${cell.binding_name}' conflicts with an existing binding or operation`,
            'validation',
            'Binding validation',
            cell.id,
            { binding_name: cell.binding_name },
          ),
        };
      }
      bindingNames.add(cell.binding_name);
    }
  }

  return { ok: true, notebook_valid: true };
}

function upstreamFailure(cellId: string, upstreamId: string): StructuredErrorData {
  return makeError(
    'UPSTREAM_FAILURE',
    `Cell '${cellId}' not executed due to upstream cell '${upstreamId}'`,
    'execution',
    'Notebook execution',
    cellId,
    { upstream_cell: upstreamId },
  );
}

export function executeNotebook(
  notebook: NotebookData,
  options?: { fail_fast?: boolean; runtime?: PipelineRuntime },
): NotebookExecutionResultData {
  const runtime = options?.runtime ?? getDefaultPipelineRuntime();
  const validation = validateNotebook(notebook, runtime);

  if (!validation.ok) {
    return {
      status: 'error',
      notebook_valid: false,
      execution_order: [],
      cell_results: {},
      bindings: {},
      error: validation.error,
    };
  }

  const failFast = options?.fail_fast ?? true;
  const cellResults: Record<string, CellResultData> = {};
  const bindings: Record<string, GeniaValue[]> = {};

  for (const cell of notebook.cells) {
    let result: CellResultData;

    if (cell.type === 'note_cell') {
      result = { status: 'skipped', cell_id: cell.id, reason: 'note_cell' };
    } else if (cell.type === 'value_cell') {
      result = {
        status: 'success',
        cell_id: cell.id,
        cell_type: cell.type,
        output: [cell.value],
      };
    } else if (cell.type === 'pipeline_cell') {
      const failedDependency = (cell.depends_on ?? []).find((depId) => {
        const depResult = cellResults[depId];
        return !depResult || depResult.status !== 'success';
      });

      if (failedDependency) {
        result = { status: 'error', cell_id: cell.id, error: upstreamFailure(cell.id, failedDependency) };
      } else {
        const pipelineResult = runtime.executePipeline(cell.pipeline);
        result = pipelineResult.success
          ? {
              status: 'success',
              cell_id: cell.id,
              cell_type: cell.type,
              output: pipelineResult.output,
              node_outputs: pipelineResult.nodeOutputs,
            }
          : {
              status: 'error',
              cell_id: cell.id,
              error:
                pipelineResult.error ??
                makeError(
                  'EXECUTION_FAILED',
                  `Pipeline execution failed for '${cell.id}'`,
                  'execution',
                  `pipeline_cell '${cell.id}'`,
                  cell.id,
                ),
            };
      }
    } else if (cell.type === 'inspect_cell') {
      const sourceResult = cellResults[cell.source_cell_id];
      result =
        sourceResult && sourceResult.status === 'success'
          ? {
              status: 'success',
              cell_id: cell.id,
              cell_type: cell.type,
              output: sourceResult.output,
            }
          : { status: 'error', cell_id: cell.id, error: upstreamFailure(cell.id, cell.source_cell_id) };
    } else {
      const bindingCell = cell as BindingCellData;
      const sourceResult = cellResults[bindingCell.source_cell_id];
      if (sourceResult && sourceResult.status === 'success') {
        bindings[bindingCell.binding_name] = sourceResult.output;
        result = {
          status: 'success',
          cell_id: bindingCell.id,
          cell_type: bindingCell.type,
          output: sourceResult.output,
        };
      } else {
        result = {
          status: 'error',
          cell_id: bindingCell.id,
          error: upstreamFailure(bindingCell.id, bindingCell.source_cell_id),
        };
      }
    }

    cellResults[cell.id] = result;

    if (result.status === 'error' && failFast) {
      return {
        status: 'error',
        notebook_valid: true,
        execution_order: notebook.cells.map((entry) => entry.id),
        cell_results: cellResults,
        bindings,
        error: result.error,
      };
    }
  }

  return {
    status: 'success',
    notebook_valid: true,
    execution_order: notebook.cells.map((cell) => cell.id),
    cell_results: cellResults,
    bindings,
  };
}

export function getPipelineCellResult(
  result: NotebookExecutionResultData,
  cellId: string,
): (CellResultSuccessData & { cell_type: 'pipeline_cell' }) | undefined {
  const cellResult = result.cell_results[cellId];
  if (!cellResult || cellResult.status !== 'success' || cellResult.cell_type !== 'pipeline_cell') {
    return undefined;
  }
  return cellResult as CellResultSuccessData & { cell_type: 'pipeline_cell' };
}
