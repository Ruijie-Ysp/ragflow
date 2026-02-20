import corpusService from '@/services/corpus-service';
import { Button, Form, Input, Select, message } from 'antd';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import SettingTitle from '../components/setting-title';
import styles from './index.less';

const { Option } = Select;

const SettingDatabase = () => {
  const { t } = useTranslation('translation', { keyPrefix: 'corpus' });
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [databases, setDatabases] = useState<string[]>([]);
  const [tables, setTables] = useState<string[]>([]);
  const [fields, setFields] = useState<string[]>([]);

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
        // Load databases after successful connection
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
      const values = await form.validateFields([
        'host',
        'port',
        'username',
        'password',
      ]);
      const { data } = await corpusService.getDatabaseList(values);

      if (data?.data?.databases) {
        setDatabases(data.data.databases);
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to load databases');
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
        setFields([]);
        form.setFieldsValue({ table: undefined, primaryField: undefined });
      }
    } catch (error: any) {
      message.error(error.message || 'Failed to load tables');
    }
  };

  const handleTableChange = async (table: string) => {
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
        setFields(data.data.fields);
        form.setFieldsValue({ primaryField: undefined });
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
        description={t('databaseConfigDescription')}
      />

      <Form form={form} layout="vertical" className={styles.databaseForm}>
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

        <Form.Item
          label={t('table')}
          name="table"
          rules={[{ required: true, message: t('tableRequired') }]}
        >
          <Select
            placeholder={t('selectTable')}
            onChange={handleTableChange}
            disabled={tables.length === 0}
          >
            {tables.map((table) => (
              <Option key={table} value={table}>
                {table}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label={t('primaryField')}
          name="primaryField"
          rules={[{ required: true, message: t('primaryFieldRequired') }]}
        >
          <Select
            placeholder={t('selectPrimaryField')}
            disabled={fields.length === 0}
          >
            {fields.map((field) => (
              <Option key={field} value={field}>
                {field}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item>
          <Button type="primary" onClick={handleSave} loading={loading}>
            {t('saveConfig')}
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default SettingDatabase;
