"""
Flowbook Notebook Core: Public API
"""

from typing import Any, Dict, Optional
from .model import Notebook, ExecutionResult, CellResult
from .schema import validate_notebook
from .executor import execute_notebook, execute_single_cell, GeniaInterpreter
from .serialize import notebook_to_dict
from .errors import FlowbookError


def load(data: Any) -> Notebook:
    """
    Load and validate a notebook from raw data.
    
    Args:
        data: JSON-compatible dictionary or object
    
    Returns:
        Validated Notebook object
    
    Raises:
        SchemaError if validation fails
    """
    return validate_notebook(data)


def validate(data: Any) -> bool:
    """
    Validate notebook data without returning the model.
    
    Args:
        data: JSON-compatible dictionary
    
    Returns:
        True if valid, False otherwise
    
    Note:
        For detailed error messages, use load() and catch SchemaError
    """
    try:
        validate_notebook(data)
        return True
    except (FlowbookError, Exception):
        return False


def execute(
    data: Any,
    interpreter: Optional[GeniaInterpreter] = None,
    fail_fast: bool = True,
) -> ExecutionResult:
    """
    Execute a notebook from raw data.
    
    Args:
        data: JSON-compatible notebook data
        interpreter: Optional Genia interpreter (uses default if not provided)
        fail_fast: If True, halt on first error (default: True)
    
    Returns:
        ExecutionResult with cell results, bindings, and errors
    
    Raises:
        SchemaError if notebook is invalid
        ReferenceError if references are invalid
        CycleError if cycles are detected
    """
    notebook = load(data)
    return execute_notebook(notebook, interpreter, fail_fast)


def execute_cell(
    data: Any,
    cell_id: str,
    interpreter: Optional[GeniaInterpreter] = None,
) -> CellResult:
    """
    Execute a single cell (re-executes dependencies).
    
    Args:
        data: JSON-compatible notebook data
        cell_id: ID of the cell to execute
        interpreter: Optional Genia interpreter
    
    Returns:
        CellResult for the target cell
    
    Raises:
        SchemaError if notebook is invalid
        ValueError if cell_id not found
    """
    notebook = load(data)
    return execute_single_cell(notebook, cell_id, interpreter)


def dump(notebook: Notebook) -> Dict[str, Any]:
    """
    Serialize a Notebook to a dictionary (Genia data).
    
    Args:
        notebook: Notebook model
    
    Returns:
        JSON-compatible dictionary
    """
    return notebook_to_dict(notebook)
