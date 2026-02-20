import kbService from '@/services/knowledge-service';
import { useQuery } from '@tanstack/react-query';

export interface VectorMetadata {
  dimension: number;
  field_name: string;
  mean: number;
  std: number;
  min: number;
  max: number;
  norm: number;
  vector?: number[];
}

export interface ChunkWithVector {
  chunk_id: string;
  content_with_weight: string;
  doc_id: string;
  docnm_kwd: string;
  important_kwd: string[];
  question_kwd: string[];
  image_id: string;
  available_int: number;
  positions: number[][];
  vector_metadata?: VectorMetadata;
}

export interface UseVectorMetadataParams {
  documentId: string;
  page: number;
  pageSize: number;
  keywords?: string;
  available?: number;
  includeVector?: boolean;
  includeFullVector?: boolean;
  enabled?: boolean;
}

export const useVectorMetadata = ({
  documentId,
  page,
  pageSize,
  keywords = '',
  available,
  includeVector = false,
  includeFullVector = false,
  enabled = true,
}: UseVectorMetadataParams) => {
  const {
    data,
    isFetching: loading,
    refetch,
  } = useQuery({
    queryKey: [
      'fetchChunkListWithVector',
      documentId,
      page,
      pageSize,
      keywords,
      available,
      includeVector,
      includeFullVector,
    ],
    placeholderData: (previousData: any) =>
      previousData ?? { data: [], total: 0, documentInfo: {} },
    gcTime: 0,
    enabled: enabled && includeVector,
    queryFn: async () => {
      const { data } = await kbService.chunk_list({
        doc_id: documentId,
        page,
        size: pageSize,
        available_int: available,
        keywords,
        include_vector: includeVector,
        include_full_vector: includeFullVector,
      });

      if (data.code === 0) {
        const res = data.data;
        return {
          data: res.chunks as ChunkWithVector[],
          total: res.total,
          documentInfo: res.doc,
        };
      }

      return {
        data: [],
        total: 0,
        documentInfo: {},
      };
    },
  });

  return {
    data: data?.data ?? [],
    total: data?.total ?? 0,
    documentInfo: data?.documentInfo ?? {},
    loading,
    refetch,
  };
};

export default useVectorMetadata;
