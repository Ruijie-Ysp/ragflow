import {
  DatabaseOutlined,
  FileTextOutlined,
  PartitionOutlined,
  ShareAltOutlined,
} from '@ant-design/icons';
import { Card, Col, Row, Statistic, Table, Typography } from 'antd';
import { useTranslation } from 'react-i18next';
import { useFetchCorpusStatistics } from './hooks';
import styles from './index.less';

const { Title } = Typography;

const KnowledgeCorpus = () => {
  const { t } = useTranslation('translation', { keyPrefix: 'corpus' });
  const { patientCount, documentStats, chunkStats, entityStats, loading } =
    useFetchCorpusStatistics();

  const documentColumns = [
    {
      title: t('byKnowledgeBase'),
      dataIndex: 'knowledgeBaseName',
      key: 'knowledgeBaseName',
    },
    {
      title: t('totalDocuments'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const chunkColumns = [
    {
      title: t('byKnowledgeBase'),
      dataIndex: 'knowledgeBaseName',
      key: 'knowledgeBaseName',
    },
    {
      title: t('totalChunks'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const entityColumns = [
    {
      title: t('byKnowledgeBase'),
      dataIndex: 'knowledgeBaseName',
      key: 'knowledgeBaseName',
    },
    {
      title: t('totalEntities'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  return (
    <div className={styles.corpusWrapper}>
      <div className={styles.header}>
        <Title level={3}>{t('title')}</Title>
        <p>{t('description')}</p>
      </div>

      <Row gutter={[16, 16]}>
        {/* 患者数据语料库卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card
            title={
              <span>
                <DatabaseOutlined className={styles.cardIcon} />
                {t('patientData')}
              </span>
            }
            bordered={false}
            className={styles.corpusCard}
            loading={loading}
          >
            <Statistic
              title={t('totalPatients')}
              value={patientCount}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        {/* 文献知识语料库卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card
            title={
              <span>
                <FileTextOutlined className={styles.cardIcon} />
                {t('documentKnowledge')}
              </span>
            }
            bordered={false}
            className={styles.corpusCard}
            loading={loading}
          >
            <Statistic
              title={t('totalDocuments')}
              value={documentStats.reduce((sum, item) => sum + item.count, 0)}
              valueStyle={{ color: '#1890ff' }}
            />
            <Table
              columns={documentColumns}
              dataSource={documentStats}
              pagination={false}
              size="small"
              className={styles.statsTable}
              rowKey="knowledgeBaseId"
            />
          </Card>
        </Col>

        {/* 向量知识语料库卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card
            title={
              <span>
                <PartitionOutlined className={styles.cardIcon} />
                {t('vectorKnowledge')}
              </span>
            }
            bordered={false}
            className={styles.corpusCard}
            loading={loading}
          >
            <Statistic
              title={t('totalChunks')}
              value={chunkStats.reduce((sum, item) => sum + item.count, 0)}
              valueStyle={{ color: '#cf1322' }}
            />
            <Table
              columns={chunkColumns}
              dataSource={chunkStats}
              pagination={false}
              size="small"
              className={styles.statsTable}
              rowKey="knowledgeBaseId"
            />
          </Card>
        </Col>

        {/* 知识图谱语料库卡片 */}
        <Col xs={24} sm={12} lg={12}>
          <Card
            title={
              <span>
                <ShareAltOutlined className={styles.cardIcon} />
                {t('knowledgeGraph')}
              </span>
            }
            bordered={false}
            className={styles.corpusCard}
            loading={loading}
          >
            <Statistic
              title={t('totalEntities')}
              value={entityStats.reduce((sum, item) => sum + item.count, 0)}
              valueStyle={{ color: '#722ed1' }}
            />
            <Table
              columns={entityColumns}
              dataSource={entityStats}
              pagination={false}
              size="small"
              className={styles.statsTable}
              rowKey="knowledgeBaseId"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default KnowledgeCorpus;
