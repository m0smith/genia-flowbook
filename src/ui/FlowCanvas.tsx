import type { FlowGraph } from '../model/types';
import NodeView from './NodeView';
import EdgeView from './EdgeView';

interface FlowCanvasProps {
  graph: FlowGraph;
  selectedNodeId: string | null;
  connectingFrom: string | null;
  onNodeClick: (id: string) => void;
  onCanvasClick: (x: number, y: number) => void;
}

export default function FlowCanvas({
  graph,
  selectedNodeId,
  connectingFrom,
  onNodeClick,
  onCanvasClick,
}: FlowCanvasProps) {
  function handleSvgClick(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    onCanvasClick(x, y);
  }

  return (
    <svg
      width={800}
      height={400}
      style={{ background: '#020617', border: '1px solid #1e293b', borderRadius: 8 }}
      onClick={handleSvgClick}
    >
      <defs>
        <marker
          id="arrow"
          markerWidth={10}
          markerHeight={7}
          refX={10}
          refY={3.5}
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
        </marker>
      </defs>

      {graph.edges.map((edge) => (
        <EdgeView key={edge.id} edge={edge} nodes={graph.nodes} />
      ))}

      {graph.nodes.map((node) => (
        <NodeView
          key={node.id}
          node={node}
          selected={selectedNodeId === node.id}
          connectingFrom={connectingFrom === node.id}
          onClick={() => onNodeClick(node.id)}
        />
      ))}
    </svg>
  );
}
