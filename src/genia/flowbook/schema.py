"""
Flowbook Notebook Core: Schema Validation and Normalization
"""

from typing import Any, Dict, List, Optional
from .model import (
    Notebook, Cell, NoteCell, ValueCell, PipelineCell, InspectCell, BindingCell,
    Pipeline, PipelineNode, PipelineEdge, NotebookMetadata, CellMetadata,
    CellType, NodeType,
)
from .errors import (
    SchemaError, make_parse_error, make_schema_error, make_duplicate_cell_id_error
)


def validate_notebook(data: Any) -> Notebook:
    """
    Parse and validate notebook data.
    
    Raises SchemaError if validation fails.
    Returns validated Notebook object.
    """
    if not isinstance(data, dict):
        raise SchemaError(make_parse_error("Notebook must be a dictionary/object"))
    
    # Extract version
    version = data.get("version", "1.0.0")
    if not isinstance(version, str):
        raise SchemaError(make_schema_error("Field 'version' must be a string"))
    
    # Extract metadata
    metadata = None
    if "metadata" in data and data["metadata"] is not None:
        metadata = _validate_notebook_metadata(data["metadata"])
    
    # Extract cells
    cells_data = data.get("cells", [])
    if not isinstance(cells_data, list):
        raise SchemaError(make_schema_error("Field 'cells' must be an array"))
    
    if len(cells_data) == 0:
        raise SchemaError(make_schema_error("Notebook must have at least one cell"))
    
    cells: List[Cell] = []
    cell_ids = []
    binding_names = set()
    reserved_names = {"source", "lines", "sum", "map", "filter", "reduce"}  # Add all reserved op names here
    for idx, cell_data in enumerate(cells_data):
        cell = _validate_cell(cell_data, idx)
        cells.append(cell)
        cell_ids.append(cell.id)
        # Check for duplicate/invalid binding names
        from .model import BindingCell
        if isinstance(cell, BindingCell):
            name = cell.binding_name
            if name in binding_names or name in reserved_names:
                from .errors import make_binding_conflict_error
                raise SchemaError(make_binding_conflict_error(name, cell.id))
            binding_names.add(name)
    # Check for duplicate cell IDs
    duplicates = [cid for cid in set(cell_ids) if cell_ids.count(cid) > 1]
    if duplicates:
        raise SchemaError(make_duplicate_cell_id_error(duplicates))
    # Check for cycles (raises CycleError, convert to SchemaError)
    try:
        from .references import build_dependency_graph
        build_dependency_graph(Notebook(version=version, cells=cells, metadata=metadata))
    except Exception as e:
        from .errors import CycleError, ReferenceError
        if isinstance(e, (CycleError, ReferenceError)):
            raise SchemaError(e.structured_error)
        raise
    return Notebook(version=version, cells=cells, metadata=metadata)


def _validate_notebook_metadata(data: Any) -> NotebookMetadata:
    """Validate notebook metadata."""
    if not isinstance(data, dict):
        raise SchemaError(make_schema_error("Metadata must be a dictionary"))
    
    return NotebookMetadata(
        author=data.get("author"),
        description=data.get("description"),
        created_at=data.get("created_at"),
        source=data.get("source"),
    )


def _validate_cell(data: Any, index: int) -> Cell:
    """Validate a single cell based on its type."""
    if not isinstance(data, dict):
        raise SchemaError(make_schema_error(f"Cell at index {index} must be a dictionary"))
    
    cell_id = data.get("id")
    if not cell_id or not isinstance(cell_id, str):
        raise SchemaError(
            make_schema_error(f"Cell at index {index} must have a 'id' field (string)")
        )
    
    cell_type = data.get("type")
    if not cell_type or cell_type not in [ct.value for ct in CellType]:
        raise SchemaError(
            make_schema_error(f"Cell '{cell_id}' has invalid type '{cell_type}'")
        )
    
    # Parse metadata
    metadata = None
    if "metadata" in data and data["metadata"] is not None:
        metadata = CellMetadata(
            label=data["metadata"].get("label"),
            custom=data["metadata"].get("custom", {}),
        )
    
    # Dispatch by cell type
    if cell_type == CellType.NOTE.value:
        return _validate_note_cell(data, cell_id, metadata)
    elif cell_type == CellType.VALUE.value:
        return _validate_value_cell(data, cell_id, metadata)
    elif cell_type == CellType.PIPELINE.value:
        return _validate_pipeline_cell(data, cell_id, metadata)
    elif cell_type == CellType.INSPECT.value:
        return _validate_inspect_cell(data, cell_id, metadata)
    elif cell_type == CellType.BINDING.value:
        return _validate_binding_cell(data, cell_id, metadata)
    else:
        raise SchemaError(make_schema_error(f"Unknown cell type '{cell_type}'"))


def _validate_note_cell(data: Dict, cell_id: str, metadata: Optional[CellMetadata]) -> NoteCell:
    """Validate a note cell."""
    content = data.get("content", "")
    if not isinstance(content, str):
        raise SchemaError(make_schema_error(f"Note cell '{cell_id}' content must be a string", cell_id))
    
    if not content:
        raise SchemaError(make_schema_error(f"Note cell '{cell_id}' content must be non-empty", cell_id))
    
    return NoteCell(id=cell_id, content=content, metadata=metadata)


def _validate_value_cell(data: Dict, cell_id: str, metadata: Optional[CellMetadata]) -> ValueCell:
    """Validate a value cell."""
    if "value" not in data:
        raise SchemaError(make_schema_error(f"Value cell '{cell_id}' must have a 'value' field", cell_id))
    
    value = data["value"]
    # Any valid JSON value is allowed (including null)
    
    return ValueCell(id=cell_id, value=value, metadata=metadata)


def _validate_pipeline_cell(data: Dict, cell_id: str, metadata: Optional[CellMetadata]) -> PipelineCell:
    """Validate a pipeline cell."""
    if "pipeline" not in data:
        raise SchemaError(make_schema_error(f"Pipeline cell '{cell_id}' must have a 'pipeline' field", cell_id))
    
    pipeline_data = data["pipeline"]
    if not isinstance(pipeline_data, dict):
        raise SchemaError(make_schema_error(f"Pipeline cell '{cell_id}' pipeline must be a dictionary", cell_id))
    
    pipeline = _validate_pipeline(pipeline_data, cell_id)
    
    # Extract depends_on
    depends_on = data.get("depends_on", [])
    if not isinstance(depends_on, list):
        raise SchemaError(make_schema_error(f"Pipeline cell '{cell_id}' depends_on must be an array", cell_id))
    
    return PipelineCell(id=cell_id, pipeline=pipeline, depends_on=depends_on, metadata=metadata)


def _validate_pipeline(data: Dict, cell_id: str) -> Pipeline:
    """Validate a pipeline object."""
    # Extract nodes
    nodes_data = data.get("nodes", [])
    if not isinstance(nodes_data, list):
        raise SchemaError(make_schema_error(f"Pipeline nodes must be an array", cell_id))
    
    nodes: List[PipelineNode] = []
    node_ids = set()
    
    for node_data in nodes_data:
        if not isinstance(node_data, dict):
            raise SchemaError(make_schema_error(f"Pipeline node must be a dictionary", cell_id))
        
        node_id = node_data.get("id")
        if not node_id or not isinstance(node_id, str):
            raise SchemaError(make_schema_error(f"Pipeline node must have 'id' field", cell_id))
        
        if node_id in node_ids:
            raise SchemaError(make_schema_error(f"Duplicate node ID '{node_id}'", cell_id))
        node_ids.add(node_id)
        
        node_type = node_data.get("type")
        if node_type not in [nt.value for nt in NodeType]:
            raise SchemaError(make_schema_error(f"Invalid node type '{node_type}'", cell_id))
        
        operation = node_data.get("operation")
        if not operation or not isinstance(operation, str):
            raise SchemaError(make_schema_error(f"Node must have 'operation' field", cell_id))
        
        node = PipelineNode(
            id=node_id,
            type=NodeType(node_type),
            operation=operation,
            x=node_data.get("x"),
            y=node_data.get("y"),
        )
        nodes.append(node)
    
    # Extract edges
    edges_data = data.get("edges", [])
    if not isinstance(edges_data, list):
        raise SchemaError(make_schema_error(f"Pipeline edges must be an array", cell_id))
    
    edges: List[PipelineEdge] = []
    edge_ids = set()
    for edge_data in edges_data:
        if not isinstance(edge_data, dict):
            raise SchemaError(make_schema_error(f"Pipeline edge must be a dictionary", cell_id))
        edge_id = edge_data.get("id")
        if not edge_id or not isinstance(edge_id, str):
            raise SchemaError(make_schema_error(f"Pipeline edge must have 'id' field", cell_id))
        if edge_id in edge_ids:
            raise SchemaError(make_schema_error(f"Duplicate edge ID '{edge_id}'", cell_id))
        edge_ids.add(edge_id)
        from_node = edge_data.get("from")
        if not from_node or from_node not in node_ids:
            raise SchemaError(make_schema_error(f"Edge references non-existent node '{from_node}'", cell_id))
        to_node = edge_data.get("to")
        if not to_node or to_node not in node_ids:
            raise SchemaError(make_schema_error(f"Edge references non-existent node '{to_node}'", cell_id))
        edge = PipelineEdge(id=edge_id, from_node=from_node, to_node=to_node)
        edges.append(edge)
    return Pipeline(nodes=nodes, edges=edges)


def _validate_inspect_cell(data: Dict, cell_id: str, metadata: Optional[CellMetadata]) -> InspectCell:
    """Validate an inspect cell."""
    source_cell_id = data.get("source_cell_id")
    if not source_cell_id or not isinstance(source_cell_id, str):
        raise SchemaError(make_schema_error(f"Inspect cell '{cell_id}' must have 'source_cell_id' field", cell_id))
    
    format_hint = data.get("format")
    if format_hint is not None and not isinstance(format_hint, str):
        raise SchemaError(make_schema_error(f"Inspect cell '{cell_id}' format must be a string or null", cell_id))
    
    return InspectCell(id=cell_id, source_cell_id=source_cell_id, format=format_hint, metadata=metadata)


def _validate_binding_cell(data: Dict, cell_id: str, metadata: Optional[CellMetadata]) -> BindingCell:
    """Validate a binding cell."""
    binding_name = data.get("binding_name")
    if not binding_name or not isinstance(binding_name, str):
        raise SchemaError(make_schema_error(f"Binding cell '{cell_id}' must have 'binding_name' field", cell_id))
    
    source_cell_id = data.get("source_cell_id")
    if not source_cell_id or not isinstance(source_cell_id, str):
        raise SchemaError(make_schema_error(f"Binding cell '{cell_id}' must have 'source_cell_id' field", cell_id))
    
    return BindingCell(id=cell_id, binding_name=binding_name, source_cell_id=source_cell_id, metadata=metadata)
