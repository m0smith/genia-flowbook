import type {
  CellResultSuccessData,
  NotebookData,
  NotebookExecutionResultData,
  StructuredErrorData,
  ValidateNotebookResult,
} from './types';

type ExecuteNotebookOptions = {
  fail_fast?: boolean;
};

type NodeProcessLike = {
  versions?: { node?: string };
  env?: Record<string, string | undefined>;
  getBuiltinModule?: (name: string) => unknown;
};

type ExecFileSyncOptions = {
  cwd: string;
  encoding: 'utf8';
  input: string;
  env: Record<string, string | undefined>;
};

type ExecFileSyncError = {
  code?: string;
  stdout?: string;
  stderr?: string;
  message?: string;
};

type ChildProcessBuiltin = {
  execFileSync: (file: string, args: string[], options: ExecFileSyncOptions) => string;
};

type UrlBuiltin = {
  fileURLToPath: (url: URL | string) => string;
};

function getNodeProcess(): NodeProcessLike | undefined {
  return (globalThis as { process?: NodeProcessLike }).process;
}

function makeError(
  code: StructuredErrorData['code'],
  message: string,
  step: StructuredErrorData['location']['step'],
  context: string,
): StructuredErrorData {
  return {
    type: 'error',
    code,
    message,
    location: { step, context },
    details: {},
  };
}

function isNodeRuntime(): boolean {
  const nodeProcess = getNodeProcess();
  return !!nodeProcess?.versions?.node && typeof nodeProcess.getBuiltinModule === 'function';
}

function browserUnavailableValidation(): ValidateNotebookResult {
  return {
    ok: false,
    notebook_valid: false,
    error: makeError(
      'EXECUTION_FAILED',
      'Flowbook validation requires the Genia-owned runtime transport; browser-side validation is disabled.',
      'execution',
      'Genia transport',
    ),
  };
}

function browserUnavailableExecution(): NotebookExecutionResultData {
  return {
    status: 'error',
    notebook_valid: false,
    execution_order: [],
    cell_results: {},
    bindings: {},
    error: makeError(
      'EXECUTION_FAILED',
      'Flowbook execution requires the Genia-owned runtime transport; browser-side execution is disabled.',
      'execution',
      'Genia transport',
    ),
  };
}

function callGeniaBridge<TResponse>(
  command: 'validate' | 'execute',
  payload: Record<string, unknown>,
): TResponse {
  if (!isNodeRuntime()) {
    throw new Error('Genia runtime transport is not available in this environment.');
  }

  const nodeProcess = getNodeProcess();
  if (!nodeProcess?.getBuiltinModule) {
    throw new Error('Genia runtime transport is not available in this environment.');
  }

  const childProcess = nodeProcess.getBuiltinModule('node:child_process') as ChildProcessBuiltin;
  const url = nodeProcess.getBuiltinModule('node:url') as UrlBuiltin;

  const srcPath = url.fileURLToPath(new URL(/* @vite-ignore */ '../../', import.meta.url));
  const cwd = url.fileURLToPath(new URL(/* @vite-ignore */ '../../../', import.meta.url));

  const pythonPath = [srcPath, nodeProcess.env?.PYTHONPATH].filter(Boolean).join(':');
  const pythonCandidates = ['python3', 'python'];

  let lastError: unknown;

  for (const executable of pythonCandidates) {
    try {
      const stdout = childProcess.execFileSync(
        executable,
        ['-m', 'genia.flowbook.host_bridge', command],
        {
          cwd,
          encoding: 'utf8',
          input: JSON.stringify(payload),
          env: {
            ...nodeProcess.env,
            PYTHONPATH: pythonPath,
          },
        },
      );

      return JSON.parse(stdout) as TResponse;
    } catch (error) {
      const candidateError = error as ExecFileSyncError;
      if (candidateError.code === 'ENOENT') {
        lastError = error;
        continue;
      }

      const stderr = typeof candidateError.stderr === 'string' ? candidateError.stderr.trim() : '';
      const stdout = typeof candidateError.stdout === 'string' ? candidateError.stdout.trim() : '';
      throw new Error(stderr || stdout || candidateError.message);
    }
  }

  throw lastError instanceof Error
    ? lastError
    : new Error('Failed to invoke the Genia-owned Flowbook host bridge.');
}

export function validateNotebook(notebook: NotebookData): ValidateNotebookResult {
  if (!isNodeRuntime()) {
    return browserUnavailableValidation();
  }

  try {
    return callGeniaBridge<ValidateNotebookResult>('validate', { notebook });
  } catch (error) {
    return {
      ok: false,
      notebook_valid: false,
      error: makeError(
        'EXECUTION_FAILED',
        error instanceof Error ? error.message : 'Validation transport failed.',
        'execution',
        'Genia transport',
      ),
    };
  }
}

export function executeNotebook(
  notebook: NotebookData,
  options?: ExecuteNotebookOptions,
): NotebookExecutionResultData {
  if (!isNodeRuntime()) {
    return browserUnavailableExecution();
  }

  try {
    return callGeniaBridge<NotebookExecutionResultData>('execute', {
      notebook,
      fail_fast: options?.fail_fast ?? true,
    });
  } catch (error) {
    return {
      status: 'error',
      notebook_valid: false,
      execution_order: [],
      cell_results: {},
      bindings: {},
      error: makeError(
        'EXECUTION_FAILED',
        error instanceof Error ? error.message : 'Execution transport failed.',
        'execution',
        'Genia transport',
      ),
    };
  }
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
