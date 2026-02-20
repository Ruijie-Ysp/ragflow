import VectorStatisticsSummary from '@/components/vector-statistics-summary';
import useVectorMetadata, {
  ChunkWithVector,
} from '@/hooks/use-vector-metadata';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import { Button, Card, List, Space, Switch, message } from 'antd';
import React, { useState } from 'react';

interface VectorTabProps {
  documentId: string;
  page: number;
  pageSize: number;
  keywords?: string;
  available?: number;
}

export const VectorTab: React.FC<VectorTabProps> = ({
  documentId,
  page,
  pageSize,
  keywords,
  available,
}) => {
  const [includeVector, setIncludeVector] = useState(false);
  const [includeFullVector, setIncludeFullVector] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState<ChunkWithVector | null>(
    null,
  );

  const { data, total, loading } = useVectorMetadata({
    documentId,
    page,
    pageSize,
    keywords,
    available,
    includeVector,
    includeFullVector,
    enabled: true,
  });

  const handleDownloadVector = (chunk: ChunkWithVector) => {
    if (!chunk.vector_metadata?.vector) {
      message.warning('请先启用"包含完整向量"选项');
      return;
    }

    const vectorData = {
      chunk_id: chunk.chunk_id,
      content: chunk.content_with_weight,
      vector: chunk.vector_metadata.vector,
      metadata: {
        dimension: chunk.vector_metadata.dimension,
        norm: chunk.vector_metadata.norm,
        mean: chunk.vector_metadata.mean,
        std: chunk.vector_metadata.std,
      },
    };

    const blob = new Blob([JSON.stringify(vectorData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vector_${chunk.chunk_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('向量数据已下载');
  };

  const handleDownloadAllVectors = () => {
    if (!includeFullVector) {
      message.warning('请先启用"包含完整向量"选项');
      return;
    }

    const chunksWithVectors = data.filter((c) => c.vector_metadata?.vector);
    if (chunksWithVectors.length === 0) {
      message.warning('没有可下载的向量数据');
      return;
    }

    const allVectors = chunksWithVectors.map((chunk) => ({
      chunk_id: chunk.chunk_id,
      content: chunk.content_with_weight.substring(0, 100) + '...',
      vector: chunk.vector_metadata!.vector,
      metadata: {
        dimension: chunk.vector_metadata!.dimension,
        norm: chunk.vector_metadata!.norm,
      },
    }));

    const blob = new Blob([JSON.stringify(allVectors, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `all_vectors_${documentId}.json`;
    a.click();
    URL.revokeObjectURL(url);
    message.success(`已下载 ${chunksWithVectors.length} 个向量`);
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card size="small">
        <Space>
          <span>显示向量元数据:</span>
          <Switch
            checked={includeVector}
            onChange={setIncludeVector}
            loading={loading}
          />
          <span style={{ marginLeft: 16 }}>包含完整向量:</span>
          <Switch
            checked={includeFullVector}
            onChange={setIncludeFullVector}
            disabled={!includeVector}
            loading={loading}
          />
          {includeFullVector && (
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownloadAllVectors}
              disabled={!data.length}
            >
              下载所有向量
            </Button>
          )}
        </Space>
      </Card>

      {includeVector && data.length > 0 && (
        <VectorStatisticsSummary chunks={data} />
      )}

      <List
        loading={loading}
        dataSource={data}
        renderItem={(chunk) => (
          <List.Item
            key={chunk.chunk_id}
            actions={[
              chunk.vector_metadata && (
                <Button
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => setSelectedChunk(chunk)}
                >
                  查看详情
                </Button>
              ),
            ]}
          >
            <List.Item.Meta
              title={chunk.docnm_kwd}
              description={chunk.content_with_weight.substring(0, 200) + '...'}
            />
          </List.Item>
        )}
      />
    </Space>
  );
};

export default VectorTab;
