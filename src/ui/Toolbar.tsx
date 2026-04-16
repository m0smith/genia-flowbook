import type { NodeType } from '../model/types';

interface ToolbarProps {
  onAddNode: (type: NodeType) => void;
  onRun: () => void;
  onReset: () => void;
  connectingFrom: string | null;
}

export default function Toolbar({ onAddNode, onRun, onReset, connectingFrom }: ToolbarProps) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
      <button onClick={() => onAddNode('source')}>Add Source</button>
      <button onClick={() => onAddNode('transform')}>Add Transform</button>
      <button onClick={() => onAddNode('sink')}>Add Sink</button>
      <button onClick={onRun} style={{ background: '#22c55e', color: '#000' }}>
        Run Pipeline
      </button>
      <button onClick={onReset}>Reset</button>
      {connectingFrom && (
        <span style={{ color: '#facc15', fontStyle: 'italic' }}>
          Connecting from <strong>{connectingFrom}</strong> — click target node
        </span>
      )}
    </div>
  );
}
