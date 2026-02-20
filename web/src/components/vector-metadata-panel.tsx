import { VectorMetadata } from '@/hooks/use-vector-metadata';
import { DownloadOutlined, LineChartOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Row,
  Statistic,
  Tag,
} from 'antd';
import React from 'react';

const { Panel } = Collapse;

interface VectorMetadataPanelProps {
  metadata: VectorMetadata;
  chunkId?: string;
  onDownload?: () => void;
  onVisualize?: () => void;
}

export const VectorMetadataPanel: React.FC<VectorMetadataPanelProps> = ({
  metadata,
  chunkId,
  onDownload,
  onVisualize,
}) => {
  if (!metadata) {
    return null;
  }

  const formatNumber = (num: number, decimals: number = 4) => {
    return num.toFixed(decimals);
  };

  return (
    <Card
      size="small"
      title={
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>向量元数据</span>
          <div>
            {onVisualize && (
              <Button
                size="small"
                icon={<LineChartOutlined />}
                onClick={onVisualize}
                style={{ marginRight: 8 }}
              >
                可视化
              </Button>
            )}
            {onDownload && metadata.vector && (
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={onDownload}
              >
                下载向量
              </Button>
            )}
          </div>
        </div>
      }
    >
      <Row gutter={16}>
        <Col span={8}>
          <Statistic title="向量维度" value={metadata.dimension} suffix="维" />
        </Col>
        <Col span={8}>
          <Statistic
            title="向量范数"
            value={formatNumber(metadata.norm)}
            precision={4}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="字段名称"
            value={metadata.field_name}
            valueStyle={{ fontSize: 14 }}
          />
        </Col>
      </Row>

      <Descriptions size="small" column={2} style={{ marginTop: 16 }} bordered>
        <Descriptions.Item label="均值">
          {formatNumber(metadata.mean)}
        </Descriptions.Item>
        <Descriptions.Item label="标准差">
          {formatNumber(metadata.std)}
        </Descriptions.Item>
        <Descriptions.Item label="最小值">
          {formatNumber(metadata.min)}
        </Descriptions.Item>
        <Descriptions.Item label="最大值">
          {formatNumber(metadata.max)}
        </Descriptions.Item>
      </Descriptions>

      {metadata.vector && (
        <Collapse ghost style={{ marginTop: 16 }}>
          <Panel
            header={`完整向量数据 (${metadata.vector.length} 个值)`}
            key="1"
          >
            <div
              style={{
                maxHeight: 200,
                overflow: 'auto',
                fontSize: 12,
                fontFamily: 'monospace',
                background: '#f5f5f5',
                padding: 8,
                borderRadius: 4,
              }}
            >
              [
              {metadata.vector.map((v, i) => (
                <span key={i}>
                  {formatNumber(v, 6)}
                  {i < metadata.vector!.length - 1 ? ', ' : ''}
                  {(i + 1) % 5 === 0 && i < metadata.vector!.length - 1
                    ? '\n'
                    : ''}
                </span>
              ))}
              ]
            </div>
          </Panel>
        </Collapse>
      )}

      {chunkId && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          Chunk ID: <Tag>{chunkId}</Tag>
        </div>
      )}
    </Card>
  );
};

export default VectorMetadataPanel;
