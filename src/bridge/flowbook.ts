import { executeNotebook as executeCoreNotebook, validateNotebook as validateCoreNotebook } from '../core/flowbook';
import type { ExecuteNotebookRequest, NotebookExecutionResultData, ValidateNotebookResult } from './types';

// Temporary in-process bridge for the React host. This is intentionally thin:
// it passes notebook-shaped data into Flowbook core and returns core-owned
// execution results without reinterpreting semantics in the host layer.
export function executeNotebook(request: ExecuteNotebookRequest): NotebookExecutionResultData {
  return executeCoreNotebook(request.notebook, {
    fail_fast: request.options?.fail_fast,
  });
}

export function validateNotebook(request: ExecuteNotebookRequest): ValidateNotebookResult {
  return validateCoreNotebook(request.notebook);
}

