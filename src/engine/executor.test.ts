import { describe, it, expect } from 'vitest';
import { executeGraph } from './executor';
import { createNode, createEdge, createGraph } from '../model';

function makeDefaultGraph() {
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

describe('executeGraph', () => {
  it('executes the default pipeline and returns [15]', () => {
    const graph = makeDefaultGraph();
    const result = executeGraph(graph);
    expect(result.success).toBe(true);
    expect(result.output).toEqual([15]);
  });

  it('captures intermediate node outputs', () => {
    const graph = makeDefaultGraph();
    const result = executeGraph(graph);
    expect(result.nodeOutputs['n1']).toEqual(['1\n2\n3\n4\n5']);
    expect(result.nodeOutputs['n2']).toEqual(['1', '2', '3', '4', '5']);
    expect(result.nodeOutputs['n3']).toEqual([1, 2, 3, 4, 5]);
    expect(result.nodeOutputs['n4']).toEqual([15]);
  });

  it('returns error for unknown operation', () => {
    const nodes = [createNode('n1', 'source', 'nonexistent', 0, 0)];
    const graph = createGraph(nodes, []);
    const result = executeGraph(graph);
    expect(result.success).toBe(false);
    expect(result.error).toContain('nonexistent');
  });
});
