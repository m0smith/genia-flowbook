import { describe, it, expect } from 'vitest';
import { createNode, createEdge, createGraph } from './index';

describe('model factories', () => {
  it('createNode returns correct shape', () => {
    const node = createNode('n1', 'source', 'source', 100, 200);
    expect(node).toEqual({ id: 'n1', type: 'source', operation: 'source', x: 100, y: 200 });
  });

  it('createEdge returns correct shape', () => {
    const edge = createEdge('n1', 'n2');
    expect(edge).toEqual({ id: 'n1->n2', from: 'n1', to: 'n2' });
  });

  it('createGraph returns correct shape', () => {
    const node = createNode('n1', 'source', 'source', 0, 0);
    const edge = createEdge('n1', 'n1');
    const graph = createGraph([node], [edge]);
    expect(graph.nodes).toHaveLength(1);
    expect(graph.edges).toHaveLength(1);
  });
});
