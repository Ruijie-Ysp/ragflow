import corpusService from '@/services/corpus-service';
import { useCallback, useEffect, useState } from 'react';

interface CorpusStats {
  kb_id: string;
  kb_name: string;
  count: number;
}

export const useFetchCorpusStatistics = () => {
  const [patientCount, setPatientCount] = useState(0);
  const [orderCount, setOrderCount] = useState(0);
  const [recordCount, setRecordCount] = useState(0);
  const [examCount, setExamCount] = useState(0);
  const [labCount, setLabCount] = useState(0);
  const [documentStats, setDocumentStats] = useState<CorpusStats[]>([]);
  const [chunkStats, setChunkStats] = useState<CorpusStats[]>([]);
  const [entityStats, setEntityStats] = useState<CorpusStats[]>([]);
  const [graphNodeStats, setGraphNodeStats] = useState<CorpusStats[]>([]);
  const [graphNodeTotal, setGraphNodeTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchStatistics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await corpusService.getCorpusStatistics();
      if (response?.data?.code === 0) {
        const data = response.data.data;
        setPatientCount(data.patient_count || 0);
        setOrderCount(data.order_count || 0);
        setRecordCount(data.record_count || 0);
        setExamCount(data.exam_count || 0);
        setLabCount(data.lab_count || 0);
        setDocumentStats(data.document_stats || []);
        setChunkStats(data.chunk_stats || []);
        setEntityStats(data.entity_stats || []);

        const graphStats: CorpusStats[] = data.graph_node_stats || [];
        setGraphNodeStats(graphStats);
        if (typeof data.graph_node_total === 'number') {
          setGraphNodeTotal(data.graph_node_total);
        } else {
          setGraphNodeTotal(
            graphStats.reduce((sum, item) => sum + (item.count || 0), 0),
          );
        }
      }
    } catch (error) {
      console.error('Failed to fetch corpus statistics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    patientCount,
    orderCount,
    recordCount,
    examCount,
    labCount,
    documentStats,
    chunkStats,
    entityStats,
    graphNodeStats,
    graphNodeTotal,
    loading,
    refetch: fetchStatistics,
  };
};

export const useFetchDatabaseConfig = () => {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const response = await corpusService.getDatabaseConfig();
      if (response?.data?.code === 0) {
        setConfig(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch database config:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return {
    config,
    loading,
    refetch: fetchConfig,
  };
};
