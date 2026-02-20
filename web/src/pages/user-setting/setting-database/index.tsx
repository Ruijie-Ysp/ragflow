import corpusService from '@/services/corpus-service';
import { Button, Collapse, Divider, Form, Input, Select, message } from 'antd';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import SettingTitle from '../components/setting-title';
import styles from './index.less';

const { Option } = Select;
const { Panel } = Collapse;

const SettingDatabase = () => {
  const { t } = useTranslation('translation', { keyPrefix: 'corpus' });
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [databases, setDatabases] = useState<string[]>([]);
  const [tables, setTables] = useState<string[]>([]);
  const [patientFields, setPatientFields] = useState<string[]>([]);
  const [orderFields, setOrderFields] = useState<string[]>([]);
  const [recordFields, setRecordFields] = useState<string[]>([]);
  const [examFields, setExamFields] = useState<string[]>([]);
  const [labFields, setLabFields] = useState<string[]>([]);

  // Load existing configuration on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const { data } = await corpusService.getDatabaseConfig();
      if (data?.data && data.data.host) {
        form.setFieldsValue(data.data);

        setTimeout(() => {
          const values = form.getFieldsValue([
            'host',
            'port',
            'username',
            'password',
            'database',
          ]);
          if (values.host && values.username && values.password) {
            handleLoadDatabases();
            if (values.database) {
              handleDatabaseChange(values.database);
            }
          }
        }, 100);
      }
    } catch (error: any) {
      console.error('Failed to load config:', error);
    }
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields([
        'host',
        'port',
        'username',
        'password',
      ]);
      setTestLoading(true);

      const { data } = await corpusService.testDatabaseConnection(values);

      if (data?.data?.success) {
        message.success(t('connectionSuccess'));
        handleLoadDatabases();
      } else {
        message.error(data?.data?.message || t('connectionFailed'));
      }
    } catch (error: any) {
      message.error(error.message || t('connectionFailed'));
    } finally {
      setTestLoading(false);
    }
  };

  const handleLoadDatabases = async () => {
    try {
      const values = form.getFieldsValue([
        'host',
        'port',
        'username',
        'password',
      ]);

      if (!values.host || !values.username || !values.password) {
        return;
      }

      const { data } = await corpusService.getDatabaseList(values);

      if (data?.data?.databases) {
        setDatabases(data.data.databases);
      }
    } catch (error: any) {
      console.error('Failed to load databases:', error);
    }
  };

  const handleDatabaseChange = async (database: string) => {
    try {
      const values = await form.validateFields([
        'host',
        'port',
        'username',
        'password',
      ]);
      const { data } = await corpusService.getTableList({
        ...values,
        database,
      });

      if (data?.data?.tables) {
        setTables(data.data.tables);
        // Clear all table and field selections
        form.setFieldsValue({
          patientTable: undefined,
          patientField: undefined,
          orderTable: undefined,
          orderField: undefined,
          recordTable: undefined,
          recordField: undefined,
          examTable: undefined,
          examField: undefined,
          labTable: undefined,
          labField: undefined,
        });
        setPatientFields([]);
        setOrderFields([]);
        setRecordFields([]);
        setExamFields([]);
        setLabFields([]);
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to load tables');
    }
  };

  const handleTableChange = async (table: string, type: string) => {
    if (!table) {
      switch (type) {
        case 'patient':
          setPatientFields([]);
          form.setFieldsValue({ patientField: undefined });
          break;
        case 'order':
          setOrderFields([]);
          form.setFieldsValue({ orderField: undefined });
          break;
        case 'record':
          setRecordFields([]);
          form.setFieldsValue({ recordField: undefined });
          break;
        case 'exam':
          setExamFields([]);
          form.setFieldsValue({ examField: undefined });
          break;
        case 'lab':
          setLabFields([]);
          form.setFieldsValue({ labField: undefined });
          break;
      }
      return;
    }

    try {
      const values = await form.validateFields([
        'host',
        'port',
        'username',
        'password',
        'database',
      ]);
      const { data } = await corpusService.getTableFields({ ...values, table });

      if (data?.data?.fields) {
        switch (type) {
          case 'patient':
            setPatientFields(data.data.fields);
            form.setFieldsValue({ patientField: undefined });
            break;
          case 'order':
            setOrderFields(data.data.fields);
            form.setFieldsValue({ orderField: undefined });
            break;
          case 'record':
            setRecordFields(data.data.fields);
            form.setFieldsValue({ recordField: undefined });
            break;
          case 'exam':
            setExamFields(data.data.fields);
            form.setFieldsValue({ examField: undefined });
            break;
          case 'lab':
            setLabFields(data.data.fields);
            form.setFieldsValue({ labField: undefined });
            break;
        }
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to load fields');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      await corpusService.saveDatabaseConfig(values);
      message.success(t('saveSuccess'));
    } catch (error: any) {
      message.error(error.message || t('saveFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.databaseWrapper}>
      <SettingTitle
        title={t('databaseConfig')}
        description={t('medicalDataConfigDescription')}
      />

      <Form form={form} layout="vertical" className={styles.databaseForm}>
        {/* Database Connection Settings */}
        <Divider orientation="left">{t('databaseConfig')}</Divider>

        <Form.Item
          label={t('host')}
          name="host"
          rules={[{ required: true, message: t('hostRequired') }]}
        >
          <Input placeholder="127.0.0.1" />
        </Form.Item>

        <Form.Item
          label={t('port')}
          name="port"
          initialValue={3306}
          rules={[{ required: true, message: t('portRequired') }]}
        >
          <Input type="number" placeholder="3306" />
        </Form.Item>

        <Form.Item
          label={t('username')}
          name="username"
          rules={[{ required: true, message: t('usernameRequired') }]}
        >
          <Input placeholder="root" />
        </Form.Item>

        <Form.Item
          label={t('password')}
          name="password"
          rules={[{ required: true, message: t('passwordRequired') }]}
        >
          <Input.Password placeholder={t('password')} />
        </Form.Item>

        <Form.Item>
          <Button
            type="default"
            onClick={handleTestConnection}
            loading={testLoading}
          >
            {t('testConnection')}
          </Button>
        </Form.Item>

        <Form.Item
          label={t('database')}
          name="database"
          rules={[{ required: true, message: t('databaseRequired') }]}
        >
          <Select
            placeholder={t('selectDatabase')}
            onChange={handleDatabaseChange}
            disabled={databases.length === 0}
          >
            {databases.map((db) => (
              <Option key={db} value={db}>
                {db}
              </Option>
            ))}
          </Select>
        </Form.Item>

        {/* Medical Data Tables Configuration */}
        <Divider orientation="left">{t('medicalDataConfig')}</Divider>

        <Collapse defaultActiveKey={['patient']} ghost>
          {/* Patient Table */}
          <Panel header={t('patientTable')} key="patient">
            <Form.Item label={t('patientTable')} name="patientTable">
              <Select
                placeholder={t('selectPatientTable')}
                onChange={(table) => handleTableChange(table, 'patient')}
                disabled={tables.length === 0}
                allowClear
              >
                {tables.map((table) => (
                  <Option key={table} value={table}>
                    {table}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label={t('patientField')} name="patientField">
              <Select
                placeholder={t('selectPrimaryField')}
                disabled={patientFields.length === 0}
                allowClear
              >
                {patientFields.map((field) => (
                  <Option key={field} value={field}>
                    {field}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Panel>

          {/* Medical Order Table */}
          <Panel header={t('orderTable')} key="order">
            <Form.Item label={t('orderTable')} name="orderTable">
              <Select
                placeholder={t('selectOrderTable')}
                onChange={(table) => handleTableChange(table, 'order')}
                disabled={tables.length === 0}
                allowClear
              >
                {tables.map((table) => (
                  <Option key={table} value={table}>
                    {table}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label={t('orderField')} name="orderField">
              <Select
                placeholder={t('selectPrimaryField')}
                disabled={orderFields.length === 0}
                allowClear
              >
                {orderFields.map((field) => (
                  <Option key={field} value={field}>
                    {field}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Panel>

          {/* Medical Record Table */}
          <Panel header={t('recordTable')} key="record">
            <Form.Item label={t('recordTable')} name="recordTable">
              <Select
                placeholder={t('selectRecordTable')}
                onChange={(table) => handleTableChange(table, 'record')}
                disabled={tables.length === 0}
                allowClear
              >
                {tables.map((table) => (
                  <Option key={table} value={table}>
                    {table}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label={t('recordField')} name="recordField">
              <Select
                placeholder={t('selectPrimaryField')}
                disabled={recordFields.length === 0}
                allowClear
              >
                {recordFields.map((field) => (
                  <Option key={field} value={field}>
                    {field}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Panel>

          {/* Examination Report Table */}
          <Panel header={t('examTable')} key="exam">
            <Form.Item label={t('examTable')} name="examTable">
              <Select
                placeholder={t('selectExamTable')}
                onChange={(table) => handleTableChange(table, 'exam')}
                disabled={tables.length === 0}
                allowClear
              >
                {tables.map((table) => (
                  <Option key={table} value={table}>
                    {table}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label={t('examField')} name="examField">
              <Select
                placeholder={t('selectPrimaryField')}
                disabled={examFields.length === 0}
                allowClear
              >
                {examFields.map((field) => (
                  <Option key={field} value={field}>
                    {field}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Panel>

          {/* Lab Report Table */}
          <Panel header={t('labTable')} key="lab">
            <Form.Item label={t('labTable')} name="labTable">
              <Select
                placeholder={t('selectLabTable')}
                onChange={(table) => handleTableChange(table, 'lab')}
                disabled={tables.length === 0}
                allowClear
              >
                {tables.map((table) => (
                  <Option key={table} value={table}>
                    {table}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label={t('labField')} name="labField">
              <Select
                placeholder={t('selectPrimaryField')}
                disabled={labFields.length === 0}
                allowClear
              >
                {labFields.map((field) => (
                  <Option key={field} value={field}>
                    {field}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Panel>
        </Collapse>

        <Form.Item style={{ marginTop: 24 }}>
          <Button type="primary" onClick={handleSave} loading={loading}>
            {t('saveConfig')}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default SettingDatabase;
