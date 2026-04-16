import type { FlowNode } from '../model/types';

interface NodeViewProps {
  node: FlowNode;
  selected: boolean;
  connectingFrom: boolean;
  onClick: () => void;
}

const STROKE: Record<string, string> = {
  source: '#22c55e',
  transform: '#3b82f6',
  sink: '#ef4444',
};

export default function NodeView({ node, selected, connectingFrom, onClick }: NodeViewProps) {
  const stroke = STROKE[node.type] ?? '#888';
  const highlight = selected || connectingFrom;

  return (
    <g
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      style={{ cursor: 'pointer' }}
    >
      <rect
        x={node.x - 60}
        y={node.y - 25}
        width={120}
        height={50}
        rx={6}
        fill={highlight ? '#1e293b' : '#0f172a'}
        stroke={highlight ? '#facc15' : stroke}
        strokeWidth={highlight ? 3 : 2}
      />
      <text
        x={node.x}
        y={node.y - 4}
        textAnchor="middle"
        fill="#f1f5f9"
        fontSize={12}
        fontFamily="monospace"
      >
        {node.operation}
      </text>
      <text
        x={node.x}
        y={node.y + 13}
        textAnchor="middle"
        fill={stroke}
        fontSize={10}
        fontFamily="sans-serif"
      >
        {node.type}
      </text>
    </g>
  );
}
