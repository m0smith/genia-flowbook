import type {
  GeniaValue,
  PipelineData,
  PipelineExecutionResult,
  PipelineNodeData,
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

function topologicalOrder(pipeline: PipelineData): string[] | null {
  const inDegree: Record<string, number> = {};
  const children: Record<string, string[]> = {};

  for (const node of pipeline.nodes) {
    inDegree[node.id] = 0;
    children[node.id] = [];
  }

  for (const edge of pipeline.edges) {
    inDegree[edge.to] = (inDegree[edge.to] ?? 0) + 1;
    children[edge.from]?.push(edge.to);
  }

  const queue = pipeline.nodes
    .filter((node) => inDegree[node.id] === 0)
    .map((node) => node.id);
  const order: string[] = [];

  while (queue.length > 0) {
    const current = queue.shift()!;
    order.push(current);

    for (const child of children[current] ?? []) {
      inDegree[child] -= 1;
      if (inDegree[child] === 0) {
        queue.push(child);
      }
    }
  }

  return order.length === pipeline.nodes.length ? order : null;
}

function nodeById(pipeline: PipelineData, nodeId: string): PipelineNodeData {
  const node = pipeline.nodes.find((candidate) => candidate.id === nodeId);
  if (!node) {
    throw new Error(`Unknown node "${nodeId}"`);
  }
  return node;
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

class CompatibilityPipelineRuntime implements PipelineRuntime {
  private readonly operations = COMPATIBILITY_OPERATIONS;

  listOperations(): string[] {
    return Object.keys(this.operations);
  }

  executePipeline(pipeline: PipelineData): PipelineExecutionResult {
    const order = topologicalOrder(pipeline);
    const nodeOutputs: Record<string, GeniaValue[]> = {};

    if (order === null) {
      return {
        success: false,
        output: [],
        nodeOutputs,
        error: makeError('CYCLE_DETECTED', 'Graph contains a cycle', 'Pipeline validation'),
      };
    }

    const parents: Record<string, string[]> = {};
    for (const node of pipeline.nodes) {
      parents[node.id] = [];
    }
    for (const edge of pipeline.edges) {
      parents[edge.to].push(edge.from);
    }

    for (const nodeId of order) {
      const node = nodeById(pipeline, nodeId);
      const operation = this.operations[node.operation];

      if (!operation) {
        return {
          success: false,
          output: [],
          nodeOutputs,
          error: makeError(
            'UNKNOWN_OPERATION',
            `Operation '${node.operation}' is not registered`,
            `Node '${nodeId}'`,
            {
              operation: node.operation,
              available_operations: this.listOperations(),
            },
          ),
        };
      }

      const input = (parents[nodeId] ?? []).flatMap((parentId) => nodeOutputs[parentId] ?? []);

      try {
        nodeOutputs[nodeId] = operation(input);
      } catch (error) {
        return {
          success: false,
          output: [],
          nodeOutputs,
          error: makeError(
            'EXECUTION_FAILED',
            `Execution failed in node '${nodeId}': ${String(error)}`,
            `Node '${nodeId}'`,
            { operation: node.operation },
          ),
        };
      }
    }

    const lastNodeId = order[order.length - 1];
    return {
      success: true,
      output: nodeOutputs[lastNodeId] ?? [],
      nodeOutputs,
    };
  }
}

let defaultRuntime: PipelineRuntime = new CompatibilityPipelineRuntime();

export function getDefaultPipelineRuntime(): PipelineRuntime {
  return defaultRuntime;
}

export function getCompatibilityOperationRegistry(): Readonly<Record<string, OperationFn>> {
  return COMPATIBILITY_OPERATIONS;
}
