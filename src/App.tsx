import { useState } from 'react';
import type { FlowGraph } from './model/types';
import type { NodeType } from './model/types';
import { createNode, createEdge, createGraph } from './model';
import type { NotebookExecutionResultData } from './bridge/types';
import { executeNotebook } from './bridge/flowbook';
import { prototypeGraphToNotebook, PROTOTYPE_PIPELINE_CELL_ID } from './bridge/adapters';
import FlowCanvas from './ui/FlowCanvas';
import Toolbar from './ui/Toolbar';

function makeDefaultGraph(): FlowGraph {
  const nodes = [
    createNode('n1', 'source', 'source', 100, 200),
    createNode('n2', 'transform', 'lines', 300, 200),
    createNode('n3', 'transform', 'map(parse_int)', 500, 200),
    createNode('n4', 'sink', 'sum', 700, 200),
  ];
  const edges = [
    createEdge('n1', 'n2'),
    createEdge('n2', 'n3'),
    createEdge('n3', 'n4'),
  ];
  return createGraph(nodes, edges);
}

let _idCounter = 10;
function newId() {
  return `node-${++_idCounter}`;
}

const NODE_OPS: Record<NodeType, string> = {
  source: 'source',
  transform: 'lines',
  sink: 'sum',
};

export default function App() {
  const [graph, setGraph] = useState<FlowGraph>(makeDefaultGraph);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [result, setResult] = useState<NotebookExecutionResultData | null>(null);

  function handleNodeClick(id: string) {
    if (connectingFrom === null) {
      setSelectedNodeId(id);
    } else {
      if (connectingFrom !== id) {
        const edge = createEdge(connectingFrom, id);
        setGraph((g) => createGraph(g.nodes, [...g.edges, edge]));
      }
      setConnectingFrom(null);
    }
  }

  function handleCanvasClick(_x: number, _y: number) {
    setSelectedNodeId(null);
    if (connectingFrom !== null) setConnectingFrom(null);
  }

  function handleAddNode(type: NodeType) {
    const x = 80 + Math.floor(Math.random() * 620);
    const y = 80 + Math.floor(Math.random() * 240);
    const id = newId();
    const node = createNode(id, type, NODE_OPS[type], x, y);
    setGraph((g) => createGraph([...g.nodes, node], g.edges));
    setSelectedNodeId(id);
    setConnectingFrom(null);
  }

  function handleRun() {
    setResult(
      executeNotebook({
        notebook: prototypeGraphToNotebook(graph),
      }),
    );
  }

  function handleReset() {
    setGraph(makeDefaultGraph());
    setSelectedNodeId(null);
    setConnectingFrom(null);
    setResult(null);
  }

  const pipelineResult =
    result?.cell_results[PROTOTYPE_PIPELINE_CELL_ID] &&
    result.cell_results[PROTOTYPE_PIPELINE_CELL_ID].status === 'success' &&
    result.cell_results[PROTOTYPE_PIPELINE_CELL_ID].cell_type === 'pipeline_cell'
      ? result.cell_results[PROTOTYPE_PIPELINE_CELL_ID]
      : null;

  const finalOutput = pipelineResult?.output ?? [];
  const nodeOutputs = pipelineResult?.node_outputs ?? {};
  const resultError = result?.error?.message;
  const success = result?.status === 'success';

  return (
    <div style={{ padding: 24, fontFamily: 'sans-serif', background: '#0a0f1e', minHeight: '100vh', color: '#f1f5f9' }}>
      <h1 style={{ marginBottom: 16, fontSize: 22, letterSpacing: 1 }}>⚙ Genia Flowbook</h1>

      <Toolbar
        onAddNode={handleAddNode}
        onConnect={() => setConnectingFrom(selectedNodeId)}
        onRun={handleRun}
        onReset={handleReset}
        selectedNodeId={selectedNodeId}
        connectingFrom={connectingFrom}
      />

      <div style={{ marginTop: 16 }}>
        <FlowCanvas
          graph={graph}
          selectedNodeId={selectedNodeId}
          connectingFrom={connectingFrom}
          onNodeClick={handleNodeClick}
          onCanvasClick={handleCanvasClick}
        />
      </div>

      <div style={{ marginTop: 8, fontSize: 12, color: '#64748b' }}>
        Click a node to select it. To connect nodes: select a node, then click another node while
        holding the connect intent via the toolbar buttons.
      </div>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>
            Execution Result:{' '}
            <span style={{ color: success ? '#22c55e' : '#ef4444' }}>
              {success ? 'SUCCESS' : 'ERROR'}
            </span>
          </h2>
          {resultError && (
            <p style={{ color: '#ef4444', fontFamily: 'monospace' }}>{resultError}</p>
          )}
          <table style={{ borderCollapse: 'collapse', fontSize: 13, fontFamily: 'monospace' }}>
            <thead>
              <tr>
                <th style={{ padding: '4px 12px', textAlign: 'left', borderBottom: '1px solid #1e293b' }}>Node</th>
                <th style={{ padding: '4px 12px', textAlign: 'left', borderBottom: '1px solid #1e293b' }}>Operation</th>
                <th style={{ padding: '4px 12px', textAlign: 'left', borderBottom: '1px solid #1e293b' }}>Output</th>
              </tr>
            </thead>
            <tbody>
              {graph.nodes.map((node) => (
                <tr key={node.id}>
                  <td style={{ padding: '4px 12px', color: '#94a3b8' }}>{node.id}</td>
                  <td style={{ padding: '4px 12px', color: '#38bdf8' }}>{node.operation}</td>
                  <td style={{ padding: '4px 12px', color: '#f1f5f9' }}>
                    {nodeOutputs[node.id] !== undefined
                      ? JSON.stringify(nodeOutputs[node.id])
                      : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ marginTop: 8, color: '#facc15' }}>
            Final output: <strong>{JSON.stringify(finalOutput)}</strong>
          </p>
        </div>
      )}
    </div>
  );
}
