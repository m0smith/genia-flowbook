export type NodeType = 'source' | 'transform' | 'sink';

export interface FlowNode {
  id: string;
  type: NodeType;
  operation: string;
  x: number;
  y: number;
}

export interface FlowEdge {
  id: string;
  from: string;
  to: string;
}

export interface FlowGraph {
  nodes: FlowNode[];
  edges: FlowEdge[];
}
