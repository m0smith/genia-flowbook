import type { FlowNode, FlowEdge, FlowGraph } from './types';
export type { NodeType, FlowNode, FlowEdge, FlowGraph } from './types';

export function createNode(
  id: string,
  type: FlowNode['type'],
  operation: string,
  x: number,
  y: number,
): FlowNode {
  return { id, type, operation, x, y };
}

export function createEdge(from: string, to: string): FlowEdge {
  const id = `${from}->${to}`;
  return { id, from, to };
}

export function createGraph(nodes: FlowNode[], edges: FlowEdge[]): FlowGraph {
  return { nodes, edges };
}
