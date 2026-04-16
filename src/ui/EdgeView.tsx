import type { FlowEdge, FlowNode } from '../model/types';

interface EdgeViewProps {
  edge: FlowEdge;
  nodes: FlowNode[];
}

function center(node: FlowNode) {
  return { x: node.x, y: node.y };
}

export default function EdgeView({ edge, nodes }: EdgeViewProps) {
  const from = nodes.find((n) => n.id === edge.from);
  const to = nodes.find((n) => n.id === edge.to);
  if (!from || !to) return null;

  const f = center(from);
  const t = center(to);

  return (
    <line
      x1={f.x + 60}
      y1={f.y}
      x2={t.x - 60}
      y2={t.y}
      stroke="#64748b"
      strokeWidth={2}
      markerEnd="url(#arrow)"
    />
  );
}
