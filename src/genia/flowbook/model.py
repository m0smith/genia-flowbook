"""
Flowbook Notebook Core: Data Model

Core immutable data structures representing the notebook spec.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Optional, Dict, List, Union
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class CellType(Enum):
    """Cell type discriminant."""
    NOTE = "note_cell"
    VALUE = "value_cell"
    PIPELINE = "pipeline_cell"
    INSPECT = "inspect_cell"
    BINDING = "binding_cell"


class NodeType(Enum):
    """Pipeline node type."""
    SOURCE = "source"
    TRANSFORM = "transform"
    SINK = "sink"


class ExecutionStatus(Enum):
    """Result of cell execution."""
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


# ============================================================================
# Notebook Structure
# ============================================================================

@dataclass(frozen=True)
class NotebookMetadata:
    """Notebook-level metadata."""
    author: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    source: Optional[str] = None


@dataclass(frozen=True)
class CellMetadata:
    """Cell-level metadata."""
    label: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Allow frozen dataclass to set defaults
        if self.custom is None:
            object.__setattr__(self, 'custom', {})


# ============================================================================
# Cell Specifications (discriminated union)
# ============================================================================

@dataclass(frozen=True)
class CellBase:
    """Base for all cells."""
    id: str
    type: CellType
    metadata: Optional[CellMetadata] = None


@dataclass(frozen=True)
class NoteCell(CellBase):
    """Markdown/text cell. Non-executable."""
    content: str = ""
    type: CellType = field(default=CellType.NOTE, init=False)


@dataclass(frozen=True)
class ValueCell(CellBase):
    """Literal value cell."""
    value: Any = None
    type: CellType = field(default=CellType.VALUE, init=False)


@dataclass(frozen=True)
class PipelineNode:
    """Node in a pipeline DAG."""
    id: str
    type: NodeType
    operation: str
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass(frozen=True)
class PipelineEdge:
    """Edge in a pipeline DAG."""
    id: str
    from_node: str = field(metadata={'json_key': 'from'})
    to_node: str = field(metadata={'json_key': 'to'})


@dataclass(frozen=True)
class Pipeline:
    """A directed acyclic graph of operations."""
    nodes: List[PipelineNode] = field(default_factory=list)
    edges: List[PipelineEdge] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineCell(CellBase):
    """Cell containing a pipeline DAG."""
    pipeline: Pipeline = field(default_factory=Pipeline)
    depends_on: List[str] = field(default_factory=list)
    type: CellType = field(default=CellType.PIPELINE, init=False)


@dataclass(frozen=True)
class InspectCell(CellBase):
    """Cell that displays outputs of another cell."""
    source_cell_id: str = ""
    format: Optional[str] = None
    type: CellType = field(default=CellType.INSPECT, init=False)


@dataclass(frozen=True)
class BindingCell(CellBase):
    """Cell that binds a name to another cell's output."""
    binding_name: str = ""
    source_cell_id: str = ""
    type: CellType = field(default=CellType.BINDING, init=False)


# Union type for all cells
Cell = Union[NoteCell, ValueCell, PipelineCell, InspectCell, BindingCell]


@dataclass(frozen=True)
class Notebook:
    """A complete notebook: ordered sequence of cells."""
    version: str = "1.0.0"
    cells: List[Cell] = field(default_factory=list)
    metadata: Optional[NotebookMetadata] = None


# ============================================================================
# Execution Results
# ============================================================================

@dataclass(frozen=True)
class CellResultSuccess:
    """Successful cell execution."""
    status: ExecutionStatus = field(default=ExecutionStatus.SUCCESS, init=False)
    cell_id: str = ""
    cell_type: CellType = CellType.NOTE
    output: List[Any] = field(default_factory=list)
    executed_at: Optional[str] = None


@dataclass(frozen=True)
class CellResultError:
    """Failed cell execution."""
    status: ExecutionStatus = field(default=ExecutionStatus.ERROR, init=False)
    cell_id: str = ""
    error: 'StructuredError' = None
    executed_at: Optional[str] = None


@dataclass(frozen=True)
class CellResultSkipped:
    """Skipped cell (not executed)."""
    status: ExecutionStatus = field(default=ExecutionStatus.SKIPPED, init=False)
    cell_id: str = ""
    reason: str = ""


CellResult = Union[CellResultSuccess, CellResultError, CellResultSkipped]


@dataclass(frozen=True)
class ExecutionResult:
    """Result of notebook execution."""
    status: Literal["success", "error"] = "success"
    cell_results: Dict[str, CellResult] = field(default_factory=dict)
    bindings: Dict[str, Any] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    error: Optional['StructuredError'] = None


# ============================================================================
# Error Reporting
# ============================================================================

@dataclass(frozen=True)
class ErrorLocation:
    """Where an error occurred."""
    step: Literal["parsing", "validation", "execution"] = "execution"
    context: str = ""


@dataclass(frozen=True)
class StructuredError:
    """Machine-readable error with context."""
    type: Literal["error"] = "error"
    code: str = ""
    message: str = ""
    location: ErrorLocation = field(default_factory=ErrorLocation)
    cell_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None


# ============================================================================
# Reference Resolution
# ============================================================================

@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    cell_id: str
    cell_type: CellType
    direct_dependencies: set = field(default_factory=set)
    transitive_dependencies: set = field(default_factory=set)


@dataclass
class DependencyGraph:
    """Computed dependency graph."""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    topological_order: List[str] = field(default_factory=list)
    has_cycle: bool = False


@dataclass
class ExecutionContext:
    """Mutable state during notebook execution."""
    notebook: Notebook
    cell_results: Dict[str, CellResult] = field(default_factory=dict)
    bindings: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, StructuredError] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    halted: bool = False
