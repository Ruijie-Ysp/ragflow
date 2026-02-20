# RAGFlow 警告修复指南

## 当前警告分析

从日志中发现以下警告:

### 1. ⚠️ SECRET_KEY 警告
```
WARNING: Using auto-generated SECRET_KEY. Generated key: 648bc60e35148fce49eebf259aa4da6f6cbd6fdac4a780f593e5448bc89a9986
```

**影响**: 每次重启服务时会生成新的密钥,可能导致会话失效

**解决方案**: 在 `docker/.env` 中添加固定的 SECRET_KEY

### 2. ⚠️ term.freq 加载失败
```
WARNING: Load term.freq FAIL!
```

**影响**: 中文分词功能可能受影响,但不影响基本功能

**原因**: 缺少中文词频文件

### 3. ⚠️ Redis 连接失败
```
WARNING: Realtime synonym is disabled, since no redis connection.
```

**影响**: 实时同义词功能被禁用

**原因**: Redis 服务可能未启动或连接配置有问题

### 4. ℹ️ 过期的任务执行器
```
INFO: task_executor_d6c0cfca8c97_0 expired, removed
INFO: task_executor_18a8d5b3b0a7_1 expired, removed
```

**影响**: 无影响,这是正常的清理过程

**说明**: 旧容器的执行器自动过期并被移除

---

## 修复步骤

### 修复 1: 设置固定的 SECRET_KEY

在 `docker/.env` 文件末尾添加:

```bash
# 固定的 SECRET_KEY (用于会话加密)
# 使用日志中生成的密钥,或者生成新的
SECRET_KEY=648bc60e35148fce49eebf259aa4da6f6cbd6fdac4a780f593e5448bc89a9986
```

### 修复 2: 检查 Redis 连接

检查 Redis 服务状态:

```bash
# 查看 Redis 容器状态
docker ps | grep redis

# 测试 Redis 连接
docker exec -it <redis-container-name> redis-cli -a infini_rag_flow ping
```

如果 Redis 未运行,检查 `docker/.env` 中的配置:

```bash
REDIS_HOST=redis
REDIS_PORT=16379
REDIS_PASSWORD=infini_rag_flow
```

### 修复 3: term.freq 文件 (可选)

这个警告通常不影响英文使用,如果需要优化中文分词:

1. 检查是否有 `term.freq` 文件
2. 确保文件路径正确
3. 如果缺失,可以从官方仓库获取

---

## 验证修复

修复后重启服务:

```bash
cd docker
docker compose down
docker compose up -d
```

检查日志:

```bash
docker compose logs -f ragflow-server | grep -i warning
```

---

## 当前服务状态总结

### ✅ 正常运行
- Elasticsearch: 健康
- 任务执行器: 4个活跃
- OpenAI Proxy: 正常
- 版本: v0.21.0-72-g0e549e96 slim

### ⚠️ 需要关注
- SECRET_KEY: 建议设置固定值
- Redis: 需要检查连接
- term.freq: 可选优化

### 📊 性能指标
- 任务队列: pending=0, lag=0, done=0, failed=0
- 内存限制: 6GB (从 .env 配置)
- 并发任务: 10 (MAX_CONCURRENT_TASKS)

---

## 建议的配置优化

基于你的 30GB 内存系统,当前配置已经比较合理:

```bash
# 当前配置 (docker/.env)
MEM_LIMIT=6442450944              # 6GB for ES
EMBEDDING_BATCH_SIZE=64           # 适中
DOC_BULK_SIZE=6                   # 适中
MAX_CONCURRENT_TASKS=10           # 适中
MAX_CONCURRENT_CHUNK_BUILDERS=3   # 保守
```

如果系统资源充足,可以考虑:

```bash
# 可选的性能提升配置
MAX_CONCURRENT_TASKS=15           # 增加并发
MAX_CONCURRENT_CHUNK_BUILDERS=5   # 增加分块并发
EMBEDDING_BATCH_SIZE=128          # 增加批处理
```

---

## 下一步

1. ✅ 添加 SECRET_KEY 到 .env
2. ✅ 检查 Redis 连接
3. ✅ 重启服务验证
4. ✅ 监控日志确认警告消失

