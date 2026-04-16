export type {
  BindingCellData,
  CellData,
  CellResultData,
  NotebookData,
  NotebookExecutionResultData,
  PipelineCellData,
  PipelineEdgeData,
  PipelineNodeData,
  StructuredErrorData,
  ValidateNotebookResult,
} from '../core/flowbook';

export interface ExecuteNotebookRequest {
  notebook: import('../core/flowbook').NotebookData;
  options?: {
    fail_fast?: boolean;
  };
}

