import VectorMetadataPanel from '@/components/vector-metadata-panel';
import VectorStatisticsSummary from '@/components/vector-statistics-summary';
import type { ChunkWithVector } from '@/hooks/use-vector-metadata';
import kbService from '@/services/knowledge-service';
import { DownloadOutlined } from '@ant-design/icons';
import {
  Button,
  List,
  Modal,
  Pagination,
  Spin,
  Switch,
  Tabs,
  message,
} from 'antd';
import React, { useEffect, useState } from 'react';

interface VectorModalProps {
  visible: boolean;
  onCancel: () => void;
  documentId: string;
}

const VectorModal: React.FC<VectorModalProps> = ({
  visible,
  onCancel,
  documentId,
}) => {
  const [includeVector, setIncludeVector] = useState(true);
  const [includeFullVector, setIncludeFullVector] = useState(false);
  const [loading, setLoading] = useState(false);
  const [chunks, setChunks] = useState<ChunkWithVector[]>([]);
  const [allChunks, setAllChunks] = useState<ChunkWithVector[]>([]); // 存储所有 chunk 用于统计
  const [selectedChunk, setSelectedChunk] = useState<ChunkWithVector | null>(
    null,
  );
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);

  useEffect(() => {
    if (visible && documentId && includeVector) {
      fetchAllVectorData();
    }
  }, [visible, documentId, includeVector, includeFullVector]);

  // 获取所有向量数据用于统计
  const fetchAllVectorData = async () => {
    setLoading(true);
    try {
      // 首先获取第一页以获取 total 数量
      const { data: firstPageData } = await kbService.chunk_list({
        doc_id: documentId,
        page: 1,
        size: pageSize,
        include_vector: includeVector,
        include_full_vector: includeFullVector,
      });

      if (firstPageData.code !== 0) {
        message.error('获取向量数据失败');
        return;
      }

      const totalCount = firstPageData.data.total || 0;
      setTotal(totalCount);
      setChunks(firstPageData.data.chunks || []);

      // 如果总数超过一页，需要获取所有页面的数据用于统计
      if (totalCount > pageSize) {
        const totalPages = Math.ceil(totalCount / pageSize);
        const allChunksData: ChunkWithVector[] = [
          ...(firstPageData.data.chunks || []),
        ];

        // 并行获取剩余页面的数据
        const promises = [];
        for (let page = 2; page <= totalPages; page++) {
          promises.push(
            kbService.chunk_list({
              doc_id: documentId,
              page: page,
              size: pageSize,
              include_vector: includeVector,
              include_full_vector: includeFullVector,
            }),
          );
        }

        const results = await Promise.all(promises);
        results.forEach(({ data }) => {
          if (data.code === 0 && data.data.chunks) {
            allChunksData.push(...data.data.chunks);
          }
        });

        setAllChunks(allChunksData);
      } else {
        setAllChunks(firstPageData.data.chunks || []);
      }
    } catch (error) {
      message.error('获取向量数据失败: ' + error);
    } finally {
      setLoading(false);
    }
  };

  // 分页切换时获取对应页面数据
  const handlePageChange = async (page: number) => {
    setCurrentPage(page);
    setLoading(true);
    try {
      const { data } = await kbService.chunk_list({
        doc_id: documentId,
        page: page,
        size: pageSize,
        include_vector: includeVector,
        include_full_vector: includeFullVector,
      });

      if (data.code === 0) {
        setChunks(data.data.chunks || []);
      }
    } catch (error) {
      message.error('获取向量数据失败: ' + error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAll = () => {
    if (!includeFullVector) {
      message.warning('请先启用"包含完整向量"选项');
      return;
    }

    // 使用 allChunks 下载所有向量
    const chunksWithVectors = allChunks.filter(
      (c) => c.vector_metadata?.vector,
    );
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

  const items = [
    {
      key: 'summary',
      label: '向量统计',
      // 使用 allChunks 进行统计，确保统计所有 chunk
      children: <VectorStatisticsSummary chunks={allChunks} />,
    },
    {
      key: 'list',
      label: `Chunk 列表 (${total} 条)`,
      children: (
        <>
          <List
            loading={loading}
            dataSource={chunks}
            renderItem={(chunk) => (
              <List.Item
                key={chunk.chunk_id}
                onClick={() => setSelectedChunk(chunk)}
                style={{ cursor: 'pointer' }}
              >
                <List.Item.Meta
                  title={`Chunk ID: ${chunk.chunk_id}`}
                  description={
                    <>
                      <div>
                        {chunk.content_with_weight.substring(0, 100)}...
                      </div>
                      {chunk.vector_metadata && (
                        <div
                          style={{ marginTop: 8, fontSize: 12, color: '#666' }}
                        >
                          维度: {chunk.vector_metadata.dimension} | 范数:{' '}
                          {chunk.vector_metadata.norm.toFixed(4)}
                        </div>
                      )}
                    </>
                  }
                />
              </List.Item>
            )}
          />
          {total > pageSize && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Pagination
                current={currentPage}
                total={total}
                pageSize={pageSize}
                onChange={handlePageChange}
                showSizeChanger={false}
                showTotal={(t) => `共 ${t} 条`}
              />
            </div>
          )}
        </>
      ),
    },
    selectedChunk && {
      key: 'detail',
      label: '详细信息',
      children: selectedChunk.vector_metadata && (
        <VectorMetadataPanel
          metadata={selectedChunk.vector_metadata}
          chunkId={selectedChunk.chunk_id}
        />
      ),
    },
  ].filter(Boolean);

  return (
    <Modal
      title="向量数据查看器"
      open={visible}
      onCancel={onCancel}
      width={900}
      footer={null}
    >
      <div style={{ marginBottom: 16 }}>
        <span style={{ marginRight: 16 }}>包含完整向量:</span>
        <Switch checked={includeFullVector} onChange={setIncludeFullVector} />
        {includeFullVector && (
          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownloadAll}
            style={{ marginLeft: 16 }}
          >
            下载所有向量
          </Button>
        )}
      </div>
      <Spin spinning={loading}>
        <Tabs items={items as any} />
      </Spin>
    </Modal>
  );
};

export default VectorModal;
