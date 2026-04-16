export type GeniaValue =
  | null
  | boolean
  | number
  | string
  | GeniaValue[]
  | { [key: string]: GeniaValue };

export type CellType =
  | 'note_cell'
  | 'value_cell'
  | 'pipeline_cell'
  | 'inspect_cell'
  | 'binding_cell';

export type PipelineNodeType = 'source' | 'transform' | 'sink';

export interface NotebookMetadata {
  author?: string;
  description?: string;
  created_at?: string;
  source?: string;
}

export interface CellMetadata {
  label?: string;
  custom?: Record<string, unknown>;
}

export interface CellBaseData {
  id: string;
  type: CellType;
  metadata?: CellMetadata;
}

export interface NoteCellData extends CellBaseData {
  type: 'note_cell';
  content: string;
}

export interface ValueCellData extends CellBaseData {
  type: 'value_cell';
  value: GeniaValue;
}

export interface PipelineNodeData {
  id: string;
  type: PipelineNodeType;
  operation: string;
  x?: number;
  y?: number;
}

export interface PipelineEdgeData {
  id: string;
  from: string;
  to: string;
}

export interface PipelineData {
  nodes: PipelineNodeData[];
  edges: PipelineEdgeData[];
}

export interface PipelineCellData extends CellBaseData {
  type: 'pipeline_cell';
  pipeline: PipelineData;
  depends_on?: string[];
}

export interface InspectCellData extends CellBaseData {
  type: 'inspect_cell';
  source_cell_id: string;
  format?: string;
}

export interface BindingCellData extends CellBaseData {
  type: 'binding_cell';
  binding_name: string;
  source_cell_id: string;
}

export type CellData =
  | NoteCellData
  | ValueCellData
  | PipelineCellData
  | InspectCellData
  | BindingCellData;

export interface NotebookData {
  version: string;
  metadata?: NotebookMetadata;
  cells: CellData[];
}

export type StructuredErrorCode =
  | 'PARSE_ERROR'
  | 'INVALID_SCHEMA'
  | 'DUPLICATE_CELL_ID'
  | 'UNKNOWN_OPERATION'
  | 'CYCLE_DETECTED'
  | 'FORWARD_REFERENCE'
  | 'MISSING_CELL_REFERENCE'
  | 'INVALID_BINDING_NAME'
  | 'UPSTREAM_FAILURE'
  | 'EXECUTION_FAILED';

export interface StructuredErrorData {
  type: 'error';
  code: StructuredErrorCode;
  message: string;
  location: {
    step: 'parsing' | 'validation' | 'execution';
    context: string;
  };
  cell_id?: string;
  details: Record<string, unknown>;
  timestamp?: string;
}

export interface CellResultSuccessData {
  status: 'success';
  cell_id: string;
  cell_type: CellType;
  output: GeniaValue[];
  node_outputs?: Record<string, GeniaValue[]>;
}

export interface CellResultSkippedData {
  status: 'skipped';
  cell_id: string;
  reason: string;
}

export interface CellResultErrorData {
  status: 'error';
  cell_id: string;
  error: StructuredErrorData;
}

export type CellResultData =
  | CellResultSuccessData
  | CellResultSkippedData
  | CellResultErrorData;

export interface NotebookExecutionResultData {
  status: 'success' | 'error';
  notebook_valid: boolean;
  execution_order: string[];
  cell_results: Record<string, CellResultData>;
  bindings: Record<string, GeniaValue[]>;
  error?: StructuredErrorData;
}

export interface ValidateNotebookResult {
  ok: boolean;
  notebook_valid: boolean;
  error?: StructuredErrorData;
}

export interface PipelineExecutionResult {
  success: boolean;
  output: GeniaValue[];
  nodeOutputs: Record<string, GeniaValue[]>;
  error?: StructuredErrorData;
}

