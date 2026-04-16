"""
Flowbook Notebook Core: Reference Resolution and Dependency Analysis
"""

from typing import Dict, List, Set, Optional, Tuple
from .model import (
    Notebook, Cell, CellType, PipelineCell, InspectCell, BindingCell,
    DependencyNode, DependencyGraph,
)
from .errors import (
    ReferenceError, CycleError,
    make_forward_reference_error, make_missing_cell_reference_error, make_cycle_error,
)


def build_dependency_graph(notebook: Notebook) -> DependencyGraph:
    """
    Build a dependency graph for the notebook.
    
    Validates:
    - All references point to existing cells
    - All references point to earlier cells (no forward refs)
    - No cycles exist
    
    Returns DependencyGraph with topological order.
    Raises ReferenceError or CycleError if validation fails.
    """
    # Index cells by ID
    cell_by_id: Dict[str, Tuple[Cell, int]] = {}
    for idx, cell in enumerate(notebook.cells):
        cell_by_id[cell.id] = (cell, idx)
    
    # Build dependency nodes
    nodes: Dict[str, DependencyNode] = {}
    edges: Set[Tuple[str, str]] = set()  # (from, to) tuples
    
    for idx, cell in enumerate(notebook.cells):
        direct_deps: Set[str] = set()
        # Extract dependencies based on cell type
        if isinstance(cell, PipelineCell):
            direct_deps.update(cell.depends_on)
        elif isinstance(cell, InspectCell):
            direct_deps.add(cell.source_cell_id)
        elif isinstance(cell, BindingCell):
            direct_deps.add(cell.source_cell_id)
        # NoteCell and ValueCell have no dependencies
        # Validate all dependencies exist
        for dep_id in direct_deps:
            if dep_id not in cell_by_id:
                raise ReferenceError(make_missing_cell_reference_error(cell.id, dep_id))
        # Create dependency node
        nodes[cell.id] = DependencyNode(
            cell_id=cell.id,
            cell_type=cell.type,
            direct_dependencies=direct_deps,
            transitive_dependencies=set(),
        )
        # Add edges
        for dep_id in direct_deps:
            edges.add((dep_id, cell.id))
    # Compute transitive closure
    for cell_id in nodes:
        transitive = _compute_transitive_closure(cell_id, nodes)
        nodes[cell_id].transitive_dependencies = transitive
    # Detect cycles (via topological sort failure)
    topo_order = _kahn_topological_sort(nodes, edges)
    if topo_order is None:
        from .errors import make_cycle_error, CycleError
        raise CycleError(make_cycle_error())
    # After topological sort, check for forward references
    cell_index = {cell.id: idx for idx, cell in enumerate(notebook.cells)}
    for cell_id, node in nodes.items():
        idx = cell_index[cell_id]
        for dep_id in node.direct_dependencies:
            dep_idx = cell_index[dep_id]
            if dep_idx >= idx:
                from .errors import make_forward_reference_error, ReferenceError
                raise ReferenceError(make_forward_reference_error(cell_id, dep_id, idx, dep_idx))
    return DependencyGraph(
        nodes=nodes,
        topological_order=topo_order,
        has_cycle=False,
    )
    
    # Compute transitive closure
    for cell_id in nodes:
        transitive = _compute_transitive_closure(cell_id, nodes)
        nodes[cell_id].transitive_dependencies = transitive
    
    # Detect cycles (via topological sort failure)
    topo_order = _kahn_topological_sort(nodes, edges)
    if topo_order is None:
        raise CycleError(make_cycle_error())
    
    return DependencyGraph(
        nodes=nodes,
        topological_order=topo_order,
        has_cycle=False,
    )


def _compute_transitive_closure(cell_id: str, nodes: Dict[str, DependencyNode]) -> Set[str]:
    """Compute transitive closure of dependencies for a cell."""
    if cell_id not in nodes:
        return set()
    
    closure: Set[str] = set()
    visited: Set[str] = set()
    
    def dfs(cid: str):
        if cid in visited:
            return
        visited.add(cid)
        
        if cid in nodes:
            for dep in nodes[cid].direct_dependencies:
                closure.add(dep)
                dfs(dep)
    
    dfs(cell_id)
    return closure


def _kahn_topological_sort(
    nodes: Dict[str, DependencyNode],
    edges: Set[Tuple[str, str]],
) -> Optional[List[str]]:
    """
    Topological sort using Kahn's algorithm.
    
    Returns sorted list of cell IDs, or None if cycle detected.
    """
    # Build in-degree map
    in_degree: Dict[str, int] = {cid: 0 for cid in nodes}
    adj_list: Dict[str, List[str]] = {cid: [] for cid in nodes}
    
    for from_id, to_id in edges:
        in_degree[to_id] += 1
        adj_list[from_id].append(to_id)
    
    # Start with nodes that have no incoming edges
    queue = [cid for cid in nodes if in_degree[cid] == 0]
    result = []
    
    while queue:
        # Sort for determinism
        queue.sort()
        current = queue.pop(0)
        result.append(current)
        
        for neighbor in sorted(adj_list[current]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # If we didn't visit all nodes, there's a cycle
    if len(result) != len(nodes):
        return None
    
    return result


def get_cell_id_by_index(notebook: Notebook, index: int) -> Optional[str]:
    """Get cell ID by its index in the notebook."""
    if 0 <= index < len(notebook.cells):
        return notebook.cells[index].id
    return None


def get_cell_by_id(notebook: Notebook, cell_id: str) -> Optional[Cell]:
    """Get a cell by its ID."""
    for cell in notebook.cells:
        if cell.id == cell_id:
            return cell
    return None


def get_cell_index(notebook: Notebook, cell_id: str) -> Optional[int]:
    """Get the index of a cell by its ID."""
    for idx, cell in enumerate(notebook.cells):
        if cell.id == cell_id:
            return idx
    return None
