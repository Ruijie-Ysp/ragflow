import api from '@/utils/api';
import registerServer from '@/utils/register-server';
import request from '@/utils/request';

const {
  getCorpusStatistics,
  getDatabaseConfig,
  saveDatabaseConfig,
  testDatabaseConnection,
  getDatabaseList,
  getTableList,
  getTableFields,
} = api;

const methods = {
  getCorpusStatistics: {
    url: getCorpusStatistics,
    method: 'get',
  },
  getDatabaseConfig: {
    url: getDatabaseConfig,
    method: 'get',
  },
  saveDatabaseConfig: {
    url: saveDatabaseConfig,
    method: 'post',
  },
  testDatabaseConnection: {
    url: testDatabaseConnection,
    method: 'post',
  },
  getDatabaseList: {
    url: getDatabaseList,
    method: 'post',
  },
  getTableList: {
    url: getTableList,
    method: 'post',
  },
  getTableFields: {
    url: getTableFields,
    method: 'post',
  },
} as const;

const corpusService = registerServer<keyof typeof methods>(methods, request);

export default corpusService;
