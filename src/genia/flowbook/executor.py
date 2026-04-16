"""
Flowbook Notebook Core: Execution Engine
"""

from typing import Any, Dict, Optional, List
from .model import (
    Notebook, Cell, NoteCell, ValueCell, PipelineCell, InspectCell, BindingCell,
    CellResult, CellResultSuccess, CellResultError, CellResultSkipped,
    ExecutionResult, ExecutionContext, ExecutionStatus, CellType,
)
from .references import build_dependency_graph, get_cell_by_id


class GeniaInterpreter:
    """Interface to Genia interpreter for pipeline execution."""
    
    def execute_pipeline(self, pipeline_data: Dict[str, Any], input_val: Any = None) -> Dict[str, Any]:
        """
        Execute a pipeline using the Genia interpreter.
        
        Expected to return:
        {
            "success": bool,
            "output": list,
            "error": str or None,
            "nodeOutputs": dict
        }
        """
        # This will be injected at runtime
        raise NotImplementedError("GeniaInterpreter must be injected")


def execute_notebook(
    notebook: Notebook,
    interpreter: Optional[GeniaInterpreter] = None,
    fail_fast: bool = True,
) -> ExecutionResult:
    """
    Execute a complete notebook.
    
    Args:
        notebook: The notebook to execute
        interpreter: Genia interpreter for pipeline execution
        fail_fast: If True, halt on first error. If False, continue.
    
    Returns:
        ExecutionResult with cell results, bindings, and any errors.
    """
    # Default interpreter (stub; real one injected by app layer)
    if interpreter is None:
        interpreter = _get_default_interpreter()
    
    # Build and validate dependency graph
    try:
        dep_graph = build_dependency_graph(notebook)
    except Exception as e:
        # Return validation error
        if hasattr(e, 'structured_error'):
            return ExecutionResult(
                status="error",
                error=e.structured_error,
            )
        raise
    
    # Create execution context
    context = ExecutionContext(
        notebook=notebook,
        execution_order=dep_graph.topological_order,
    )
    
    # Execute cells in topological order
    for cell_id in context.execution_order:
        if context.halted and fail_fast:
            break
        
        cell = get_cell_by_id(notebook, cell_id)
        if cell is None:
            continue
        
        result = _execute_cell(cell, context, interpreter)
        context.cell_results[cell_id] = result
        
        # Handle error
        if isinstance(result, CellResultError):
            context.errors[cell_id] = result.error
            if fail_fast:
                context.halted = True
                return _build_execution_result(context, error=result.error)
    
    # Success
    return _build_execution_result(context)


def execute_single_cell(
    notebook: Notebook,
    cell_id: str,
    interpreter: Optional[GeniaInterpreter] = None,
) -> CellResult:
    """
    Execute a single cell (MVP: requires re-executing dependencies).
    
    This is not optimized; it re-executes the entire notebook up to the target cell.
    Future optimization: cache results between executions.
    """
    # Build dependency graph
    dep_graph = build_dependency_graph(notebook)
    
    # Find target cell position in execution order
    if cell_id not in dep_graph.topological_order:
        raise ValueError(f"Cell '{cell_id}' not found in notebook")
    
    # Execute up to target cell
    if interpreter is None:
        interpreter = _get_default_interpreter()
    
    context = ExecutionContext(
        notebook=notebook,
        execution_order=dep_graph.topological_order,
    )
    
    for cid in context.execution_order:
        cell = get_cell_by_id(notebook, cid)
        if cell is None:
            continue
        
        result = _execute_cell(cell, context, interpreter)
        context.cell_results[cid] = result
        
        if cid == cell_id:
            return result
    
    raise ValueError(f"Cell '{cell_id}' not executed")


# ============================================================================
# Internal Helpers
# ============================================================================

def _execute_cell(
    cell: Cell,
    context: ExecutionContext,
    interpreter: GeniaInterpreter,
) -> CellResult:
    """Execute a single cell and return its result."""
    
    # Not executable
    if isinstance(cell, NoteCell):
        return CellResultSkipped(cell_id=cell.id, reason="note_cell")
    
    # Value cell
    if isinstance(cell, ValueCell):
        return CellResultSuccess(
            cell_id=cell.id,
            cell_type=cell.type,
            output=[cell.value],
        )
    
    # Pipeline cell
    if isinstance(cell, PipelineCell):
        return _execute_pipeline_cell(cell, context, interpreter)
    
    # Inspect cell
    if isinstance(cell, InspectCell):
        return _execute_inspect_cell(cell, context)
    
    # Binding cell
    if isinstance(cell, BindingCell):
        return _execute_binding_cell(cell, context)
    
    raise ValueError(f"Unknown cell type: {type(cell)}")


def _execute_pipeline_cell(
    cell: PipelineCell,
    context: ExecutionContext,
    interpreter: GeniaInterpreter,
) -> CellResult:
    """Execute a pipeline cell."""
    
    # Check upstream dependencies
    for dep_id in cell.depends_on:
        if dep_id not in context.cell_results:
            from .errors import make_upstream_failure_error, ExecutionError
            error = make_upstream_failure_error(cell.id, dep_id)
            return CellResultError(cell_id=cell.id, error=error)
        
        result = context.cell_results[dep_id]
        if isinstance(result, CellResultError):
            from .errors import make_upstream_failure_error, ExecutionError
            error = make_upstream_failure_error(cell.id, dep_id)
            return CellResultError(cell_id=cell.id, error=error)
    
    # Execute pipeline
    try:
        pipeline_dict = _serialize_pipeline_for_interpreter(cell.pipeline)
        exec_result = interpreter.execute_pipeline(pipeline_dict)
        
        if not exec_result.get("success", False):
            from .errors import make_execution_failed_error, ExecutionError
            error_msg = exec_result.get("error", "Unknown error")
            error = make_execution_failed_error(
                cell.id,
                "pipeline execution",
                error_msg,
                {"node_outputs": exec_result.get("nodeOutputs", {})},
            )
            return CellResultError(cell_id=cell.id, error=error)
        
        output = exec_result.get("output", [])
        return CellResultSuccess(
            cell_id=cell.id,
            cell_type=cell.type,
            output=output,
        )
    
    except Exception as e:
        from .errors import make_execution_failed_error
        error = make_execution_failed_error(cell.id, "pipeline execution", str(e))
        return CellResultError(cell_id=cell.id, error=error)


def _execute_inspect_cell(
    cell: InspectCell,
    context: ExecutionContext,
) -> CellResult:
    """Execute an inspect cell."""
    
    # Get source cell result
    if cell.source_cell_id not in context.cell_results:
        from .errors import make_upstream_failure_error
        error = make_upstream_failure_error(cell.id, cell.source_cell_id)
        return CellResultError(cell_id=cell.id, error=error)
    
    source_result = context.cell_results[cell.source_cell_id]
    
    # If source failed, propagate error
    if isinstance(source_result, CellResultError):
        from .errors import make_upstream_failure_error
        error = make_upstream_failure_error(cell.id, cell.source_cell_id)
        return CellResultError(cell_id=cell.id, error=error)
    
    # Return source output
    if isinstance(source_result, CellResultSuccess):
        return CellResultSuccess(
            cell_id=cell.id,
            cell_type=cell.type,
            output=source_result.output,
        )
    
    # Source was skipped
    return CellResultSkipped(cell_id=cell.id, reason="source_cell_skipped")


def _execute_binding_cell(
    cell: BindingCell,
    context: ExecutionContext,
) -> CellResult:
    """Execute a binding cell."""
    
    # Get source cell result
    if cell.source_cell_id not in context.cell_results:
        from .errors import make_upstream_failure_error
        error = make_upstream_failure_error(cell.id, cell.source_cell_id)
        return CellResultError(cell_id=cell.id, error=error)
    
    source_result = context.cell_results[cell.source_cell_id]
    
    # If source failed, propagate error
    if isinstance(source_result, CellResultError):
        from .errors import make_upstream_failure_error
        error = make_upstream_failure_error(cell.id, cell.source_cell_id)
        return CellResultError(cell_id=cell.id, error=error)
    
    # Bind the output
    if isinstance(source_result, CellResultSuccess):
        # Binding name points to the output array's first element
        # (or the array itself, depending on semantics)
        # For MVP: bind the array itself
        context.bindings[cell.binding_name] = source_result.output
        
        return CellResultSuccess(
            cell_id=cell.id,
            cell_type=cell.type,
            output=source_result.output,
        )
    
    # Source was skipped
    return CellResultSkipped(cell_id=cell.id, reason="source_cell_skipped")


def _serialize_pipeline_for_interpreter(pipeline: Any) -> Dict[str, Any]:
    """Convert Pipeline model to format expected by Genia interpreter."""
    nodes = []
    for node in pipeline.nodes:
        nodes.append({
            "id": node.id,
            "type": node.type.value,
            "operation": node.operation,
            "x": node.x,
            "y": node.y,
        })
    
    edges = []
    for edge in pipeline.edges:
        edges.append({
            "id": edge.id,
            "from": edge.from_node,
            "to": edge.to_node,
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
    }


def _build_execution_result(
    context: ExecutionContext,
    error: Optional[Any] = None,
) -> ExecutionResult:
    """Build ExecutionResult from context."""
    status = "error" if error or context.errors else "success"
    
    return ExecutionResult(
        status=status,
        cell_results=context.cell_results,
        bindings=context.bindings,
        execution_order=context.execution_order,
        error=error,
    )


def _get_default_interpreter() -> GeniaInterpreter:
    """Get the default interpreter (delegates to existing Genia executor)."""
    from src.engine import executeGraph
    
    class GenieFlowInterpreter(GeniaInterpreter):
        def execute_pipeline(self, pipeline_data: Dict[str, Any], input_val: Any = None) -> Dict[str, Any]:
            # Import the flow graph model and executor from the project
            from src.model import createNode, createEdge, createGraph, FlowGraph
            
            # Convert pipeline_data to FlowGraph format
            nodes = []
            for node_data in pipeline_data.get("nodes", []):
                nodes.append(createNode(
                    node_data["id"],
                    node_data["type"],
                    node_data["operation"],
                    node_data.get("x", 0),
                    node_data.get("y", 0),
                ))
            
            edges = []
            for edge_data in pipeline_data.get("edges", []):
                edges.append(createEdge(edge_data["from"], edge_data["to"]))
            
            graph = createGraph(nodes, edges)
            
            # Execute using existing executor
            result = executeGraph(graph, input_val)
            
            return {
                "success": result["success"],
                "output": result["output"],
                "error": result.get("error"),
                "nodeOutputs": result.get("nodeOutputs", {}),
            }
    
    return GenieFlowInterpreter()
