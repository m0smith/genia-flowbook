import { executeNotebook, getPipelineCellResult } from '../core/flowbook';
import { prototypeGraphToNotebook, PROTOTYPE_PIPELINE_CELL_ID } from '../bridge/adapters';
import type { FlowGraph } from '../model/types';

export interface ExecutionResult {
  success: boolean;
  output: unknown[];
  error?: string;
  nodeOutputs: Record<string, unknown[]>;
}

// Deprecated compatibility wrapper for the pre-Phase-1 graph prototype.
// The authoritative execution path now runs through Flowbook core using a
// notebook-shaped payload; this function only adapts the old graph API.
export function executeGraph(graph: FlowGraph, _input?: string): ExecutionResult {
  const notebookResult = executeNotebook(prototypeGraphToNotebook(graph));
  const pipelineResult = getPipelineCellResult(notebookResult, PROTOTYPE_PIPELINE_CELL_ID);

  if (notebookResult.status === 'error' || !pipelineResult) {
    return {
      success: false,
      output: [],
      error: notebookResult.error?.message ?? 'Notebook execution failed',
      nodeOutputs: {},
    };
  }

  return {
    success: true,
    output: pipelineResult.output,
    nodeOutputs: pipelineResult.node_outputs ?? {},
  };
}
