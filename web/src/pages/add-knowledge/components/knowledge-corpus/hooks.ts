import corpusService from '@/services/corpus-service';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

interface CorpusStats {
  knowledgeBaseId: string;
  knowledgeBaseName: string;
  count: number;
}

export const useFetchCorpusStatistics = () => {
  const [patientCount, setPatientCount] = useState(0);
  const [documentStats, setDocumentStats] = useState<CorpusStats[]>([]);
  const [chunkStats, setChunkStats] = useState<CorpusStats[]>([]);
  const [entityStats, setEntityStats] = useState<CorpusStats[]>([]);

  const { data, isFetching: loading } = useQuery({
    queryKey: ['fetchCorpusStatistics'],
    queryFn: async () => {
      const { data } = await corpusService.getCorpusStatistics();
      return data?.data ?? {};
    },
  });

  useEffect(() => {
    if (data) {
      setPatientCount(data.patientCount || 0);
      setDocumentStats(data.documentStats || []);
      setChunkStats(data.chunkStats || []);
      setEntityStats(data.entityStats || []);
    }
  }, [data]);

  return {
    patientCount,
    documentStats,
    chunkStats,
    entityStats,
    loading,
  };
};

export const useFetchDatabaseConfig = () => {
  const { data, isFetching: loading } = useQuery({
    queryKey: ['fetchDatabaseConfig'],
    queryFn: async () => {
      const { data } = await corpusService.getDatabaseConfig();
      return data?.data ?? {};
    },
  });

  return { data, loading };
};
