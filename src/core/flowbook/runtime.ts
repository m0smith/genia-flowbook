import type {
  GeniaValue,
  PipelineData,
  PipelineExecutionResult,
  StructuredErrorData,
} from './types';

export type OperationFn = (input: GeniaValue[]) => GeniaValue[];

export interface PipelineRuntime {
  executePipeline(pipeline: PipelineData): PipelineExecutionResult;
  listOperations(): string[];
}

function makeError(
  code: StructuredErrorData['code'],
  message: string,
  context: string,
  details: Record<string, unknown> = {},
): StructuredErrorData {
  return {
    type: 'error',
    code,
    message,
    location: {
      step: code === 'EXECUTION_FAILED' || code === 'UNKNOWN_OPERATION' ? 'execution' : 'validation',
      context,
    },
    details,
  };
}

function compatibilityOperations(): Record<string, OperationFn> {
  return {
    source: () => ['1\n2\n3\n4\n5'],
    lines: (input) => String(input[0] ?? '').split('\n').filter(Boolean),
    'map(parse_int)': (input) => input.map((value) => parseInt(String(value), 10)),
    sum: (input) => [input.reduce((total, value) => Number(total) + Number(value), 0)],
  };
}

const COMPATIBILITY_OPERATIONS = Object.freeze(compatibilityOperations());

class GeniaRequiredPipelineRuntime implements PipelineRuntime {
  private readonly operations = Object.keys(COMPATIBILITY_OPERATIONS);

  listOperations(): string[] {
    return this.operations;
  }

  executePipeline(_pipeline: PipelineData): PipelineExecutionResult {
    return {
      success: false,
      output: [],
      nodeOutputs: {},
      error: makeError(
        'EXECUTION_FAILED',
        'Flowbook execution requires a Genia runtime adapter; host-side pipeline execution is disabled.',
        'Pipeline execution',
      ),
    };
  }
}

let defaultRuntime: PipelineRuntime = new GeniaRequiredPipelineRuntime();

export function getDefaultPipelineRuntime(): PipelineRuntime {
  return defaultRuntime;
}

export function getCompatibilityOperationRegistry(): Readonly<Record<string, OperationFn>> {
  return COMPATIBILITY_OPERATIONS;
}
