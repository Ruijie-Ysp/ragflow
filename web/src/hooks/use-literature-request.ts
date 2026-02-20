import message from '@/components/ui/message';
import {
  ILiterature,
  ILiteratureAgentResult,
} from '@/interfaces/database/literature';
import i18n from '@/locales/config';
import literatureService from '@/services/literature-service';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'umi';
import {
  useGetPaginationWithRouter,
  useHandleSearchChange,
} from './logic-hooks';

export const enum LiteratureApiAction {
  FetchLiteratureList = 'fetchLiteratureList',
  FetchLiteratureDetail = 'fetchLiteratureDetail',
  FetchAgentResults = 'fetchAgentResults',
  UploadLiterature = 'uploadLiterature',
  ProcessLiterature = 'processLiterature',
  RunAgent = 'runAgent',
  DeleteLiterature = 'deleteLiterature',
  MineruHealth = 'mineruHealth',
}

export const useLiteratureId = (): string => {
  const { id } = useParams();
  return (id as string) || '';
};

export const useFetchLiteratureList = () => {
  const { pagination, setPagination } = useGetPaginationWithRouter();
  const { searchString, handleInputChange } = useHandleSearchChange();

  const {
    data,
    isFetching: loading,
    refetch,
  } = useQuery<{
    list: ILiterature[];
    total: number;
  }>({
    queryKey: [
      LiteratureApiAction.FetchLiteratureList,
      pagination,
      searchString,
    ],
    initialData: { list: [], total: 0 },
    queryFn: async () => {
      const { data } = await literatureService.getLiteratureList({
        page: pagination.current,
        page_size: pagination.pageSize,
        keywords: searchString,
      });
      if (data?.code === 0) {
        return data?.data ?? { list: [], total: 0 };
      }
      return { list: [], total: 0 };
    },
    // 禁用自动刷新，避免重置用户选择的配置
    refetchOnWindowFocus: false,
  });

  return {
    list: data?.list || [],
    total: data?.total || 0,
    loading,
    pagination,
    setPagination,
    searchString,
    handleInputChange,
    refetch,
  };
};

export const useFetchLiteratureDetail = (id?: string) => {
  const literatureId = useLiteratureId();
  const targetId = id || literatureId;

  const {
    data,
    isFetching: loading,
    refetch,
  } = useQuery<ILiterature | null>({
    queryKey: [LiteratureApiAction.FetchLiteratureDetail, targetId],
    initialData: null,
    queryFn: async () => {
      const { data } = await literatureService.getLiterature(targetId);
      if (data?.code === 0) {
        return data?.data ?? null;
      }
      return null;
    },
    enabled: !!targetId,
    // 禁用自动刷新，避免重置用户选择的配置
    refetchOnWindowFocus: false,
  });

  return { literature: data, loading, refetch };
};

export const useUploadLiterature = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return literatureService.uploadLiterature(formData);
    },
    onSuccess: () => {
      message.success(i18n.t('literature.uploadSuccess'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchLiteratureList],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.uploadFailed'));
    },
  });

  return { uploadLiterature: mutateAsync, loading };
};

export const useProcessLiterature = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (params: {
      literatureId: string;
      parseMethod?: string;
    }) => {
      return literatureService.processLiterature(
        params.literatureId,
        params.parseMethod || 'MinerU',
      );
    },
    onSuccess: () => {
      message.success(i18n.t('literature.processStarted'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchLiteratureList],
      });
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchLiteratureDetail],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.processFailed'));
    },
  });

  return { processLiterature: mutateAsync, loading };
};

export const useDeleteLiterature = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (literatureId: string) => {
      return literatureService.deleteLiterature(literatureId);
    },
    onSuccess: () => {
      message.success(i18n.t('literature.deleteSuccess'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchLiteratureList],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.deleteFailed'));
    },
  });

  return { deleteLiterature: mutateAsync, loading };
};

export const useCancelProcess = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (literatureId: string) => {
      return literatureService.cancelProcess(literatureId);
    },
    onSuccess: () => {
      message.success(i18n.t('literature.cancelSuccess'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchLiteratureList],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.cancelFailed'));
    },
  });

  return { cancelProcess: mutateAsync, loading };
};

export const useFetchAgentResults = (literatureId: string) => {
  const {
    data,
    isFetching: loading,
    refetch,
  } = useQuery<{
    list: ILiteratureAgentResult[];
    total: number;
  }>({
    queryKey: [LiteratureApiAction.FetchAgentResults, literatureId],
    initialData: { list: [], total: 0 },
    queryFn: async () => {
      const { data } = await literatureService.getAgentResults(literatureId);
      if (data?.code === 0) {
        return data?.data ?? { list: [], total: 0 };
      }
      return { list: [], total: 0 };
    },
    enabled: !!literatureId,
    // 禁用自动刷新，避免重置用户选择的配置
    refetchOnWindowFocus: false,
  });

  return {
    results: data?.list || [],
    total: data?.total || 0,
    loading,
    refetch,
  };
};

export const useRunAgent = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (params: {
      literatureId: string;
      agentId: string;
      agentTitle: string;
      inputSource?: string;
      maxSegmentChars?: number;
    }) => {
      return literatureService.runAgent(
        params.literatureId,
        params.agentId,
        params.agentTitle,
        params.inputSource || 'markdown',
        params.maxSegmentChars || 12000,
      );
    },
    onSuccess: () => {
      message.success(i18n.t('literature.agentStarted'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchAgentResults],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.agentFailed'));
    },
  });

  return { runAgent: mutateAsync, loading };
};

export const useDeleteAgentResult = () => {
  const queryClient = useQueryClient();

  const { mutateAsync, isPending: loading } = useMutation({
    mutationFn: async (resultId: string) => {
      return literatureService.deleteAgentResult(resultId);
    },
    onSuccess: () => {
      message.success(i18n.t('literature.deleteResultSuccess'));
      queryClient.invalidateQueries({
        queryKey: [LiteratureApiAction.FetchAgentResults],
      });
    },
    onError: () => {
      message.error(i18n.t('literature.deleteResultFailed'));
    },
  });

  return { deleteAgentResult: mutateAsync, loading };
};
