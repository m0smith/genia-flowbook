"""
Node/host bridge for the Genia-owned Flowbook runtime.

This module accepts notebook-shaped JSON on stdin and returns normalized JSON on
stdout so host-side adapters can delegate validation/execution without owning
semantics.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .api import load
from .errors import FlowbookError
from .executor import execute_notebook
from .model import (
    CellResultError,
    CellResultSkipped,
    CellResultSuccess,
    ExecutionResult,
    StructuredError,
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    command = args[0] if args else ""

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        json.dump(_fatal_error(f"Invalid JSON payload: {exc}"), sys.stdout)
        sys.stdout.write("\n")
        return 1

    try:
        if command == "validate":
            response = handle_validate(payload)
        elif command == "execute":
            response = handle_execute(payload)
        else:
            response = _fatal_error(
                "Host bridge command must be 'validate' or 'execute'."
            )
            json.dump(response, sys.stdout)
            sys.stdout.write("\n")
            return 1
    except Exception as exc:  # pragma: no cover - defensive guard
        response = _fatal_error(f"Unexpected Genia host bridge failure: {exc}")
        json.dump(response, sys.stdout)
        sys.stdout.write("\n")
        return 1

    json.dump(response, sys.stdout)
    sys.stdout.write("\n")
    return 0


def handle_validate(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        load(payload.get("notebook"))
        return {
            "ok": True,
            "notebook_valid": True,
        }
    except FlowbookError as exc:
        return {
            "ok": False,
            "notebook_valid": False,
            "error": exc.to_dict(),
        }


def handle_execute(payload: Dict[str, Any]) -> Dict[str, Any]:
    fail_fast = bool(payload.get("fail_fast", True))

    try:
        notebook = load(payload.get("notebook"))
        result = execute_notebook(notebook, fail_fast=fail_fast)
        return _execution_result_to_dict(result, notebook_valid=True)
    except FlowbookError as exc:
        return {
            "status": "error",
            "notebook_valid": False,
            "execution_order": [],
            "cell_results": {},
            "bindings": {},
            "error": exc.to_dict(),
        }


def _execution_result_to_dict(
    result: ExecutionResult,
    notebook_valid: bool,
) -> Dict[str, Any]:
    return {
        "status": result.status,
        "notebook_valid": notebook_valid,
        "execution_order": result.execution_order,
        "cell_results": {
            cell_id: _cell_result_to_dict(cell_result)
            for cell_id, cell_result in result.cell_results.items()
        },
        "bindings": result.bindings,
        "error": _structured_error_to_dict(result.error) if result.error else None,
    }


def _cell_result_to_dict(result: Any) -> Dict[str, Any]:
    if isinstance(result, CellResultSuccess):
        return {
            "status": "success",
            "cell_id": result.cell_id,
            "cell_type": result.cell_type.value,
            "output": result.output,
            "node_outputs": result.node_outputs,
        }

    if isinstance(result, CellResultError):
        return {
            "status": "error",
            "cell_id": result.cell_id,
            "error": _structured_error_to_dict(result.error),
        }

    if isinstance(result, CellResultSkipped):
        return {
            "status": "skipped",
            "cell_id": result.cell_id,
            "reason": result.reason,
        }

    raise TypeError(f"Unsupported cell result type: {type(result)}")


def _structured_error_to_dict(error: StructuredError | None) -> Dict[str, Any] | None:
    if error is None:
        return None

    return {
        "type": error.type,
        "code": error.code,
        "message": error.message,
        "location": {
            "step": error.location.step,
            "context": error.location.context,
        },
        "cell_id": error.cell_id,
        "details": error.details,
        "timestamp": error.timestamp,
    }


def _fatal_error(message: str) -> Dict[str, Any]:
    return {
        "type": "error",
        "code": "EXECUTION_FAILED",
        "message": message,
        "location": {
            "step": "execution",
            "context": "Genia host bridge",
        },
        "details": {},
    }


if __name__ == "__main__":
    raise SystemExit(main())
