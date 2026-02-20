import api from '@/utils/api';
import request from '@/utils/request';

const literatureService = {
  // 获取文献列表
  getLiteratureList: (params: {
    page?: number;
    page_size?: number;
    keywords?: string;
    status?: string;
  }) => {
    return request.get(api.literatureList, { params });
  },

  // 上传文献
  uploadLiterature: (formData: FormData) => {
    return request.post(api.literatureUpload, {
      data: formData,
    });
  },

  // 获取文献详情
  getLiterature: (id: string) => {
    return request.get(api.literatureDetail(id));
  },

  // 删除文献
  deleteLiterature: (id: string) => {
    return request.delete(api.literatureDelete(id));
  },

  // 处理文献 (支持多种解析方法)
  processLiterature: (id: string, parseMethod: string = 'MinerU') => {
    return request.post(api.literatureProcess(id), {
      data: { parse_method: parseMethod },
    });
  },

  // 获取文献原始文件
  getLiteratureFile: (id: string) => {
    return api.literatureFile(id);
  },

  // 获取智能体处理结果列表
  getAgentResults: (
    literatureId: string,
    params?: { page?: number; page_size?: number },
  ) => {
    return request.get(api.literatureAgentResults(literatureId), { params });
  },

  // 运行智能体（支持入参选择和分段大小配置）
  runAgent: (
    literatureId: string,
    agentId: string,
    agentTitle: string,
    inputSource: string = 'markdown',
    maxSegmentChars: number = 12000,
  ) => {
    return request.post(api.literatureRunAgent(literatureId), {
      data: {
        agent_id: agentId,
        agent_title: agentTitle,
        input_source: inputSource,
        max_segment_chars: maxSegmentChars,
      },
    });
  },

  // 获取智能体处理结果详情
  getAgentResult: (resultId: string) => {
    return request.get(api.literatureAgentResult(resultId));
  },

  // 删除智能体处理结果
  deleteAgentResult: (resultId: string) => {
    return request.delete(api.literatureDeleteAgentResult(resultId));
  },

  // 检查 MinerU 服务状态
  checkMineruHealth: () => {
    return request.get(api.literatureMineruHealth);
  },

  // 取消/重置处理中的任务
  cancelProcess: (id: string) => {
    return request.post(api.literatureCancelProcess(id));
  },
};

export default literatureService;
