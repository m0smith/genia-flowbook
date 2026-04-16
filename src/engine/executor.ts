import type { FlowGraph } from '../model/types';
import { OPERATIONS } from './operations';

export interface ExecutionResult {
  success: boolean;
  output: unknown[];
  error?: string;
  nodeOutputs: Record<string, unknown[]>;
}

export function executeGraph(graph: FlowGraph, _input?: string): ExecutionResult {
  const nodeOutputs: Record<string, unknown[]> = {};

  // Build adjacency for topological sort
  const inDegree: Record<string, number> = {};
  const children: Record<string, string[]> = {};

  for (const node of graph.nodes) {
    inDegree[node.id] = 0;
    children[node.id] = [];
  }
  for (const edge of graph.edges) {
    inDegree[edge.to] = (inDegree[edge.to] ?? 0) + 1;
    children[edge.from].push(edge.to);
  }

  // Kahn's algorithm
  const queue = graph.nodes.filter((n) => inDegree[n.id] === 0).map((n) => n.id);
  const order: string[] = [];

  while (queue.length > 0) {
    const current = queue.shift()!;
    order.push(current);
    for (const child of children[current]) {
      inDegree[child]--;
      if (inDegree[child] === 0) queue.push(child);
    }
  }

  if (order.length !== graph.nodes.length) {
    return { success: false, output: [], error: 'Graph contains a cycle', nodeOutputs };
  }

  // Build parent lookup
  const parents: Record<string, string[]> = {};
  for (const node of graph.nodes) parents[node.id] = [];
  for (const edge of graph.edges) parents[edge.to].push(edge.from);

  // Execute nodes in topological order
  for (const nodeId of order) {
    const node = graph.nodes.find((n) => n.id === nodeId)!;
    const op = OPERATIONS[node.operation];

    if (!op) {
      return {
        success: false,
        output: [],
        error: `Unknown operation: "${node.operation}"`,
        nodeOutputs,
      };
    }

    // Gather inputs from parent outputs
    const parentIds = parents[nodeId];
    let input: unknown[] = [];
    if (parentIds.length > 0) {
      // Flatten all parent outputs as input
      input = parentIds.flatMap((pid) => nodeOutputs[pid] ?? []);
    }

    try {
      nodeOutputs[nodeId] = op(input);
    } catch (err) {
      return {
        success: false,
        output: [],
        error: `Error in node "${nodeId}" (${node.operation}): ${String(err)}`,
        nodeOutputs,
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
