import {
  ApartmentOutlined,
  BlockOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { Card, Col, Row, Spin, Table } from 'antd';
import { useTranslation } from 'react-i18next';
import { useFetchCorpusStatistics } from './hooks';
import styles from './index.less';

const Corpus = () => {
  const { t } = useTranslation('translation', { keyPrefix: 'corpus' });
  const {
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
  } = useFetchCorpusStatistics();

  const documentColumns = [
    {
      title: t('knowledgeBaseName'),
      dataIndex: 'kb_name',
      key: 'kb_name',
    },
    {
      title: t('documentCount'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const chunkColumns = [
    {
      title: t('knowledgeBaseName'),
      dataIndex: 'kb_name',
      key: 'kb_name',
    },
    {
      title: t('chunkCount'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const entityColumns = [
    {
      title: t('knowledgeBaseName'),
      dataIndex: 'kb_name',
      key: 'kb_name',
    },
    {
      title: t('entityCount'),
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const totalEntities = entityStats.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className={styles.corpusContainer}>
      <h1 className={styles.title}>{t('title')}</h1>
      <Spin spinning={loading}>
        <Row gutter={[32, 32]} justify="center">
          {/* 患者数据语料库 */}
          <Col xs={24} sm={12} md={12} lg={6} xl={6}>
            <div className={`${styles.cardWrapper} ${styles.patientCard}`}>
              <Card>
                <div className={styles.contentWrapper}>
                  <div className={styles.cardTitle}>
                    <DatabaseOutlined
                      className={`${styles.icon} ${styles.patientIcon}`}
                    />
                    {t('patientDataCorpus')}
                  </div>
                  <div className={styles.medicalDataList}>
                    <div className={styles.medicalDataItem}>
                      <span className={styles.medicalDataLabel}>
                        {t('patients')}
                      </span>
                      <span className={styles.medicalDataValue}>
                        {patientCount}
                      </span>
                    </div>
                    <div className={styles.medicalDataItem}>
                      <span className={styles.medicalDataLabel}>
                        {t('orders')}
                      </span>
                      <span className={styles.medicalDataValue}>
                        {orderCount}
                      </span>
                    </div>
                    <div className={styles.medicalDataItem}>
                      <span className={styles.medicalDataLabel}>
                        {t('records')}
                      </span>
                      <span className={styles.medicalDataValue}>
                        {recordCount}
                      </span>
                    </div>
                    <div className={styles.medicalDataItem}>
                      <span className={styles.medicalDataLabel}>
                        {t('exams')}
                      </span>
                      <span className={styles.medicalDataValue}>
                        {examCount}
                      </span>
                    </div>
                    <div className={styles.medicalDataItem}>
                      <span className={styles.medicalDataLabel}>
                        {t('labs')}
                      </span>
                      <span className={styles.medicalDataValue}>
                        {labCount}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </Col>

          {/* 文献知识语料库 */}
          <Col xs={24} sm={12} md={12} lg={6} xl={6}>
            <div className={`${styles.cardWrapper} ${styles.documentCard}`}>
              <Card>
                <div className={styles.contentWrapper}>
                  <div className={styles.cardTitle}>
                    <FileTextOutlined
                      className={`${styles.icon} ${styles.documentIcon}`}
                    />
                    {t('documentCorpus')}
                  </div>
                  <div className={styles.totalCount}>
                    {documentStats.reduce((sum, item) => sum + item.count, 0)}
                    <span>{t('documents')}</span>
                  </div>
                  {documentStats.length > 0 && (
                    <>
                      <div className={styles.divider} />
                      <Table
                        dataSource={documentStats}
                        columns={documentColumns}
                        pagination={false}
                        size="small"
                        rowKey="kb_id"
                        className={styles.table}
                      />
                    </>
                  )}
                </div>
              </Card>
            </div>
          </Col>

          {/* 向量知识语料库 */}
          <Col xs={24} sm={12} md={12} lg={6} xl={6}>
            <div className={`${styles.cardWrapper} ${styles.vectorCard}`}>
              <Card>
                <div className={styles.contentWrapper}>
                  <div className={styles.cardTitle}>
                    <BlockOutlined
                      className={`${styles.icon} ${styles.vectorIcon}`}
                    />
                    {t('vectorCorpus')}
                  </div>
                  <div className={styles.totalCount}>
                    {chunkStats.reduce((sum, item) => sum + item.count, 0)}
                    <span>{t('chunks')}</span>
                  </div>
                  {chunkStats.length > 0 && (
                    <>
                      <div className={styles.divider} />
                      <Table
                        dataSource={chunkStats}
                        columns={chunkColumns}
                        pagination={false}
                        size="small"
                        rowKey="kb_id"
                        className={styles.table}
                      />
                    </>
                  )}
                </div>
              </Card>
            </div>
          </Col>

          {/* 知识图谱语料库 */}
          <Col xs={24} sm={12} md={12} lg={6} xl={6}>
            <div className={`${styles.cardWrapper} ${styles.graphCard}`}>
              <Card>
                <div className={styles.contentWrapper}>
                  <div className={styles.cardTitle}>
                    <ApartmentOutlined
                      className={`${styles.icon} ${styles.graphIcon}`}
                    />
                    {t('knowledgeGraphCorpus')}
                  </div>
                  <div className={styles.totalCount}>
                    {totalEntities}
                    <span>
                      {t('entities')}
                      {graphNodeTotal > 0 &&
                        ` · ${graphNodeTotal}${t('graphNodes')}`}
                    </span>
                  </div>
                  {entityStats.length > 0 && (
                    <>
                      <div className={styles.divider} />
                      <Table
                        dataSource={entityStats}
                        columns={entityColumns}
                        pagination={false}
                        size="small"
                        rowKey="kb_id"
                        className={styles.table}
                      />
                    </>
                  )}
                </div>
              </Card>
            </div>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default Corpus;
