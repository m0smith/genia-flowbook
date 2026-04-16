"""
Flowbook Notebook Core: Structured Error Types
"""

from typing import Any, Dict, Optional, Literal
from .model import ErrorLocation, StructuredError


class FlowbookError(Exception):
    """Base exception for Flowbook errors."""

    def __init__(self, structured_error: StructuredError):
        self.structured_error = structured_error
        super().__init__(structured_error.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.structured_error.type,
            "code": self.structured_error.code,
            "message": self.structured_error.message,
            "location": {
                "step": self.structured_error.location.step,
                "context": self.structured_error.location.context,
            },
            "cell_id": self.structured_error.cell_id,
            "details": self.structured_error.details,
            "timestamp": self.structured_error.timestamp,
        }


class SchemaError(FlowbookError):
    """Raised when notebook structure is invalid."""
    pass


class ReferenceError(FlowbookError):
    """Raised when a reference is invalid."""
    pass


class CycleError(FlowbookError):
    """Raised when a cycle is detected."""
    pass


class ExecutionError(FlowbookError):
    """Raised when execution fails."""
    pass


# ============================================================================
# Error Construction Helpers
# ============================================================================


def make_parse_error(message: str) -> StructuredError:
    """Create a parse error."""
    return StructuredError(
        code="PARSE_ERROR",
        message=message,
        location=ErrorLocation(step="parsing", context="Notebook parsing"),
    )


def make_schema_error(message: str, cell_id: Optional[str] = None) -> StructuredError:
    """Create a schema validation error."""
    return StructuredError(
        code="INVALID_SCHEMA",
        message=message,
        location=ErrorLocation(step="validation", context="Schema validation"),
        cell_id=cell_id,
    )


def make_duplicate_cell_id_error(cell_ids: list) -> StructuredError:
    """Create a duplicate cell ID error."""
    return StructuredError(
        code="DUPLICATE_CELL_ID",
        message=f"Duplicate cell ID(s): {', '.join(cell_ids)}",
        location=ErrorLocation(step="validation", context="Cell ID uniqueness"),
        details={"duplicates": cell_ids},
    )


def make_forward_reference_error(
    cell_id: str, target_id: str, cell_index: int, target_index: int
) -> StructuredError:
    """Create a forward reference error."""
    return StructuredError(
        code="FORWARD_REFERENCE",
        message=f"Cell '{cell_id}' references cell '{target_id}' which appears after it",
        location=ErrorLocation(step="validation", context="Reference ordering"),
        cell_id=cell_id,
        details={
            "referenced_cell": target_id,
            "cell_position": cell_index,
            "referenced_position": target_index,
        },
    )


def make_missing_cell_reference_error(cell_id: str, target_id: str) -> StructuredError:
    """Create a missing cell reference error."""
    return StructuredError(
        code="MISSING_CELL_REFERENCE",
        message=f"Cell '{cell_id}' references cell '{target_id}' which does not exist",
        location=ErrorLocation(step="validation", context="Reference resolution"),
        cell_id=cell_id,
        details={"referenced_cell": target_id},
    )


def make_cycle_error() -> StructuredError:
    """Create a cycle detection error."""
    return StructuredError(
        code="CYCLE_DETECTED",
        message="Circular dependency detected in notebook",
        location=ErrorLocation(step="validation", context="Cycle detection"),
    )


def make_unknown_operation_error(
    operation: str, cell_id: str, available_ops: Optional[list] = None
) -> StructuredError:
    """Create an unknown operation error."""
    return StructuredError(
        code="UNKNOWN_OPERATION",
        message=f"Operation '{operation}' is not registered",
        location=ErrorLocation(
            step="execution", context=f"Node in cell '{cell_id}'"
        ),
        cell_id=cell_id,
        details={
            "operation": operation,
            "available_operations": available_ops or [],
        },
    )


def make_upstream_failure_error(
    cell_id: str, upstream_cell_id: str
) -> StructuredError:
    """Create an upstream failure error."""
    return StructuredError(
        code="UPSTREAM_FAILURE",
        message=f"Cell '{cell_id}' not executed due to failure in upstream cell '{upstream_cell_id}'",
        location=ErrorLocation(step="execution", context="Upstream dependency"),
        cell_id=cell_id,
        details={"upstream_cell": upstream_cell_id},
    )


def make_execution_failed_error(
    cell_id: str, context: str, original_error: str, details: Optional[Dict] = None
) -> StructuredError:
    """Create an execution failed error."""
    return StructuredError(
        code="EXECUTION_FAILED",
        message=f"Execution failed in {context}: {original_error}",
        location=ErrorLocation(step="execution", context=context),
        cell_id=cell_id,
        details=details or {"error": original_error},
    )


def make_binding_conflict_error(binding_name: str, cell_id: str) -> StructuredError:
    """Create a binding name conflict error."""
    return StructuredError(
        code="INVALID_BINDING_NAME",
        message=f"Binding name '{binding_name}' conflicts with reserved name or already exists",
        location=ErrorLocation(step="validation", context="Binding validation"),
        cell_id=cell_id,
        details={"binding_name": binding_name},
    )
