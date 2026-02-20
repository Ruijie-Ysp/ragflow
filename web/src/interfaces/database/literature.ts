export interface ILiterature {
  id: string;
  tenant_id: string;
  created_by: string;
  name: string;
  location: string;
  size: number;
  parse_method: string; // 解析方法: MinerU, DeepDOC, PlainText, Table
  markdown_content: string | null;
  txt_content: string | null;
  process_status: '0' | '1' | '2' | '3'; // 0-待处理, 1-处理中, 2-成功, 3-失败
  process_message: string | null;
  process_begin_at: string | null;
  process_duration: number;
  permission: 'me' | 'team';
  status: '0' | '1';
  create_time: number;
  create_date: string;
  update_time: number;
  update_date: string;
  running_agent_count?: number; // 正在处理的智能体任务数量
}

export interface ILiteratureAgentResult {
  id: string;
  literature_id: string;
  agent_id: string;
  agent_title: string | null;
  version: number;
  input_content: string | null;
  output_content: string | null;
  input_source: string | null; // markdown | result:{result_id}
  segment_info: string | null; // JSON: {"total_chars": 25000, "segment_count": 3, ...}
  status: '0' | '1' | '2'; // 0-处理中, 1-成功, 2-失败
  error_message: string | null;
  process_duration: number;
  create_time: number;
  create_date: string;
  update_time: number;
  update_date: string;
}

// 分段信息接口
export interface ISegmentInfo {
  total_chars: number;
  segment_count: number;
  source: string;
  source_label: string;
}

export interface ILiteratureListResult {
  list: ILiterature[];
  total: number;
}

export interface IAgentResultListResult {
  list: ILiteratureAgentResult[];
  total: number;
}

// 处理状态枚举
export enum LiteratureProcessStatus {
  Pending = '0',
  Processing = '1',
  Success = '2',
  Failed = '3',
}

// 智能体结果状态枚举
export enum AgentResultStatus {
  Processing = '0',
  Success = '1',
  Failed = '2',
}
