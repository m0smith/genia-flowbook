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

class GeniaTransportRuntime implements PipelineRuntime {
  private readonly operations: string[] = [];

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
        'Flowbook pipeline execution is Genia-owned; the TypeScript host does not execute pipelines.',
        'Genia transport',
      ),
    };
  }
}

let defaultRuntime: PipelineRuntime = new GeniaTransportRuntime();

export function getDefaultPipelineRuntime(): PipelineRuntime {
  return defaultRuntime;
}

export function getCompatibilityOperationRegistry(): Readonly<Record<string, OperationFn>> {
  return Object.freeze({});
}
