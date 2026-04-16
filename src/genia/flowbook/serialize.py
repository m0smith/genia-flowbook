"""
Flowbook Notebook Core: Serialization
"""

from typing import Any, Dict, List
from .model import (
    Notebook, Cell, NoteCell, ValueCell, PipelineCell, InspectCell, BindingCell,
    Pipeline, PipelineNode, PipelineEdge,
)


def notebook_to_dict(notebook: Notebook) -> Dict[str, Any]:
    """
    Convert a Notebook model to a dictionary (Genia data).
    """
    cells_data = []
    for cell in notebook.cells:
        cells_data.append(_cell_to_dict(cell))
    
    result: Dict[str, Any] = {
        "version": notebook.version,
        "cells": cells_data,
    }
    
    if notebook.metadata:
        metadata_dict = {}
        if notebook.metadata.author:
            metadata_dict["author"] = notebook.metadata.author
        if notebook.metadata.description:
            metadata_dict["description"] = notebook.metadata.description
        if notebook.metadata.created_at:
            metadata_dict["created_at"] = notebook.metadata.created_at
        if notebook.metadata.source:
            metadata_dict["source"] = notebook.metadata.source
        
        if metadata_dict:
            result["metadata"] = metadata_dict
    
    return result


def _cell_to_dict(cell: Cell) -> Dict[str, Any]:
    """Convert a single cell to a dictionary."""
    cell_dict: Dict[str, Any] = {
        "id": cell.id,
        "type": cell.type.value,
    }
    
    # Add metadata if present
    if cell.metadata:
        metadata_dict = {}
        if cell.metadata.label:
            metadata_dict["label"] = cell.metadata.label
        if cell.metadata.custom:
            metadata_dict["custom"] = cell.metadata.custom
        if metadata_dict:
            cell_dict["metadata"] = metadata_dict
    
    # Type-specific fields
    if isinstance(cell, NoteCell):
        cell_dict["content"] = cell.content
    
    elif isinstance(cell, ValueCell):
        cell_dict["value"] = cell.value
    
    elif isinstance(cell, PipelineCell):
        cell_dict["pipeline"] = _pipeline_to_dict(cell.pipeline)
        if cell.depends_on:
            cell_dict["depends_on"] = cell.depends_on
    
    elif isinstance(cell, InspectCell):
        cell_dict["source_cell_id"] = cell.source_cell_id
        if cell.format:
            cell_dict["format"] = cell.format
    
    elif isinstance(cell, BindingCell):
        cell_dict["binding_name"] = cell.binding_name
        cell_dict["source_cell_id"] = cell.source_cell_id
    
    return cell_dict


def _pipeline_to_dict(pipeline: Pipeline) -> Dict[str, Any]:
    """Convert a Pipeline to a dictionary."""
    nodes_data = []
    for node in pipeline.nodes:
        node_dict = {
            "id": node.id,
            "type": node.type.value,
            "operation": node.operation,
        }
        if node.x is not None:
            node_dict["x"] = node.x
        if node.y is not None:
            node_dict["y"] = node.y
        nodes_data.append(node_dict)
    
    edges_data = []
    for edge in pipeline.edges:
        edges_data.append({
            "id": edge.id,
            "from": edge.from_node,
            "to": edge.to_node,
        })
    
    return {
        "nodes": nodes_data,
        "edges": edges_data,
    }
