# Flowbook Notebook Specification (Clarified)

## Notebook Schema
- **version**: string (default: "1.0.0") *(optional)*
- **cells**: array of cell objects *(required, non-empty)*
- **metadata**: object *(optional)*
  - **author**: string *(optional)*
  - **description**: string *(optional)*
  - **created_at**: string *(optional)*
  - **source**: string *(optional)*

## Cell Types

### note_cell
- **id**: string *(required, unique)*
- **type**: "note_cell" *(required)*
- **content**: string *(required, non-empty)*
- **metadata**: object *(optional)*

### value_cell
- **id**: string *(required, unique)*
- **type**: "value_cell" *(required)*
- **value**: any JSON value *(required)*
- **metadata**: object *(optional)*

### pipeline_cell
- **id**: string *(required, unique)*
- **type**: "pipeline_cell" *(required)*
- **pipeline**: object *(required, see below)*
- **depends_on**: array of cell IDs *(optional, default: [])*
- **metadata**: object *(optional)*

#### Pipeline Structure
- **nodes**: array of node objects *(required)*
  - **id**: string *(required, unique within pipeline)*
  - **type**: "source" | "transform" | "sink" *(required)*
  - **operation**: string *(required)*
  - **x**, **y**: float *(optional, ignored by execution)*
- **edges**: array of edge objects *(required)*
  - **id**: string *(required, unique within pipeline)*
  - **from**: node ID *(required, must exist)*
  - **to**: node ID *(required, must exist)*

### inspect_cell
- **id**: string *(required, unique)*
- **type**: "inspect_cell" *(required)*
- **source_cell_id**: string *(required, must reference earlier cell)*
- **format**: string *(optional)*
- **metadata**: object *(optional)*

### binding_cell
- **id**: string *(required, unique)*
- **type**: "binding_cell" *(required)*
- **binding_name**: string *(required, unique, valid identifier)*
- **source_cell_id**: string *(required, must reference earlier cell)*
- **metadata**: object *(optional)*

> **Note:** The binding cell binds the *entire array output* of the referenced cell, not just the first element.

## Reference Rules
- All references (`depends_on`, `source_cell_id`) must point to existing, earlier cells.
- No forward references.
- All cell IDs must be unique.
- All pipeline node and edge IDs must be unique within their pipeline.

## Execution Guarantees
- Cells execute in dependency order (topological, never forward).
- Each cell executes at most once per run.
- Errors in one cell do not affect independent cells.
- Results are cached per execution.
- Notebooks are always acyclic.
