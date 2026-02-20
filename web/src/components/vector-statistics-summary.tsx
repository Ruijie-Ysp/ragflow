import { ChunkWithVector } from '@/hooks/use-vector-metadata';
import {
  BarChartOutlined,
  DotChartOutlined,
  FunctionOutlined,
} from '@ant-design/icons';
import { Card, Col, Empty, Progress, Row, Statistic } from 'antd';
import React, { useMemo } from 'react';

interface VectorStatisticsSummaryProps {
  chunks: ChunkWithVector[];
}

export const VectorStatisticsSummary: React.FC<
  VectorStatisticsSummaryProps
> = ({ chunks }) => {
  const statistics = useMemo(() => {
    const chunksWithVector = chunks.filter((c) => c.vector_metadata);

    if (chunksWithVector.length === 0) {
      return null;
    }

    const dimensions = chunksWithVector.map(
      (c) => c.vector_metadata!.dimension,
    );
    const norms = chunksWithVector.map((c) => c.vector_metadata!.norm);
    const means = chunksWithVector.map((c) => c.vector_metadata!.mean);
    const stds = chunksWithVector.map((c) => c.vector_metadata!.std);

    const avgNorm = norms.reduce((a, b) => a + b, 0) / norms.length;
    const minNorm = Math.min(...norms);
    const maxNorm = Math.max(...norms);

    const avgMean = means.reduce((a, b) => a + b, 0) / means.length;
    const avgStd = stds.reduce((a, b) => a + b, 0) / stds.length;

    // Calculate norm distribution (for progress bar)
    const normRange = maxNorm - minNorm;
    const normProgress =
      normRange > 0 ? ((avgNorm - minNorm) / normRange) * 100 : 50;

    return {
      totalChunks: chunks.length,
      chunksWithVector: chunksWithVector.length,
      dimension: dimensions[0], // Assuming all chunks have same dimension
      avgNorm,
      minNorm,
      maxNorm,
      avgMean,
      avgStd,
      normProgress,
      coverage: (chunksWithVector.length / chunks.length) * 100,
    };
  }, [chunks]);

  if (!statistics) {
    return (
      <Card>
        <Empty description="暂无向量数据" />
      </Card>
    );
  }

  const formatNumber = (num: number, decimals: number = 4) => {
    return num.toFixed(decimals);
  };

  return (
    <Card title="向量数据统计汇总">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="总块数"
            value={statistics.totalChunks}
            prefix={<BarChartOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="包含向量"
            value={statistics.chunksWithVector}
            suffix={`/ ${statistics.totalChunks}`}
            prefix={<DotChartOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="向量维度"
            value={statistics.dimension}
            suffix="维"
            prefix={<FunctionOutlined />}
          />
        </Col>
        <Col span={6}>
          <div>
            <div style={{ marginBottom: 8, fontSize: 14, color: '#666' }}>
              向量覆盖率
            </div>
            <Progress
              percent={Number(statistics.coverage.toFixed(1))}
              status={statistics.coverage === 100 ? 'success' : 'active'}
            />
          </div>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card size="small" title="平均范数">
            <Statistic
              value={formatNumber(statistics.avgNorm)}
              precision={4}
              valueStyle={{ fontSize: 20 }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
              范围: {formatNumber(statistics.minNorm)} ~{' '}
              {formatNumber(statistics.maxNorm)}
            </div>
            <Progress
              percent={Number(statistics.normProgress.toFixed(1))}
              showInfo={false}
              strokeColor="#52c41a"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="平均均值">
            <Statistic
              value={formatNumber(statistics.avgMean)}
              precision={4}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="平均标准差">
            <Statistic
              value={formatNumber(statistics.avgStd)}
              precision={4}
              valueStyle={{ fontSize: 20 }}
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default VectorStatisticsSummary;
