# RAGFlow 任务队列管理指南

## 概述

RAGFlow使用Redis Stream作为任务队列,用于处理文档解析、知识图谱构建等异步任务。本文档介绍如何管理和清理任务队列。

## 任务队列架构

### 1. Redis Stream队列

RAGFlow使用Redis Stream实现任务队列,主要包括:

- **队列名称**:
  - `rag_flow_svr_queue` (优先级0,默认队列)
  - `rag_flow_svr_queue_1` (优先级1,高优先级队列)

- **Consumer Group**: `rag_flow_svr_task_broker`

- **任务类型**:
  - 文档解析任务
  - 知识图谱构建任务 (GraphRAG)
  - RAPTOR任务
  - Mindmap任务
  - Dataflow任务

### 2. 数据库任务记录

任务信息同时存储在MySQL数据库的`task`表中,包含:
- 任务ID
- 文档ID
- 任务类型
- 进度信息
- 处理状态

### 3. 任务取消标记

使用Redis键值对存储任务取消标记:
- 格式: `{task_id}-cancel`
- 值: `"x"`

---

## 清理任务队列

### 方法1: 使用清理脚本 (推荐)

我们提供了一个专门的清理脚本 `scripts/clear_task_queue.py`。

#### 基本用法

```bash
# 进入项目目录
cd /path/to/ragflow

# 清理所有任务(Redis队列 + 数据库)
python scripts/clear_task_queue.py --all

# 预览模式(不实际执行)
python scripts/clear_task_queue.py --all --dry-run
```

#### 高级用法

```bash
# 只清理Redis队列
python scripts/clear_task_queue.py --queue-only

# 只清理数据库任务记录
python scripts/clear_task_queue.py --db-only

# 清理指定文档的任务
python scripts/clear_task_queue.py --doc-id abc123def456

# 清理指定文档的所有相关数据
python scripts/clear_task_queue.py --all --doc-id abc123def456
```

#### 脚本功能

清理脚本会执行以下操作:

1. **清理Redis队列**:
   - 删除队列中的所有任务消息
   - 重新创建consumer group
   - 清理任务取消标记

2. **清理数据库**:
   - 删除任务记录
   - 重置文档处理状态(progress=0, run="0")

3. **日志输出**:
   - 显示清理进度
   - 统计清理数量
   - 报告错误信息

---

### 方法2: 使用Redis CLI

如果只需要清理Redis队列,可以直接使用Redis命令。

#### 连接到Redis

```bash
# 使用docker-compose环境
docker exec -it ragflow-redis redis-cli

# 或者使用本地Redis
redis-cli -h localhost -p 6379
```

#### 清理队列

```bash
# 查看队列长度
XLEN rag_flow_svr_queue
XLEN rag_flow_svr_queue_1

# 删除整个队列
DEL rag_flow_svr_queue
DEL rag_flow_svr_queue_1

# 或者使用XTRIM清空队列(保留队列结构)
XTRIM rag_flow_svr_queue MAXLEN 0
XTRIM rag_flow_svr_queue_1 MAXLEN 0

# 清理所有取消标记
KEYS *-cancel
# 然后逐个删除或使用脚本批量删除
```

#### 查看队列信息

```bash
# 查看队列信息
XINFO STREAM rag_flow_svr_queue

# 查看consumer group信息
XINFO GROUPS rag_flow_svr_queue

# 查看pending消息
XPENDING rag_flow_svr_queue rag_flow_svr_task_broker

# 查看队列中的消息
XRANGE rag_flow_svr_queue - + COUNT 10
```

---

### 方法3: 使用Python代码

如果需要在代码中清理队列,可以使用以下方式:

```python
from rag.utils.redis_conn import REDIS_CONN
from rag.settings import get_svr_queue_names, SVR_CONSUMER_GROUP_NAME
from api.db.services.task_service import TaskService
from api.db.db_models import Task

# 清理Redis队列
for queue_name in get_svr_queue_names():
    # 删除队列
    REDIS_CONN.REDIS.delete(queue_name)
    
    # 重新创建consumer group
    REDIS_CONN.REDIS.xgroup_create(
        queue_name, 
        SVR_CONSUMER_GROUP_NAME, 
        id="0", 
        mkstream=True
    )

# 清理数据库任务
Task.delete().execute()

# 清理指定文档的任务
doc_id = "your_doc_id"
TaskService.filter_delete([Task.doc_id == doc_id])
```

---

## 常见场景

### 场景1: 任务堆积,需要清空重新开始

```bash
# 1. 停止task executor服务
docker-compose stop ragflow-task-executor

# 2. 清理所有任务
python scripts/clear_task_queue.py --all

# 3. 重启task executor服务
docker-compose start ragflow-task-executor
```

### 场景2: 某个文档处理卡住

```bash
# 清理该文档的任务
python scripts/clear_task_queue.py --doc-id <document_id>

# 然后在UI中重新解析该文档
```

### 场景3: 测试环境清理

```bash
# 预览将要清理的内容
python scripts/clear_task_queue.py --all --dry-run

# 确认后执行清理
python scripts/clear_task_queue.py --all
```

### 场景4: 只清理Redis,保留数据库记录

```bash
# 只清理Redis队列和取消标记
python scripts/clear_task_queue.py --queue-only
```

---

## 监控任务队列

### 查看队列状态

```python
from rag.utils.redis_conn import REDIS_CONN
from rag.settings import get_svr_queue_name, SVR_CONSUMER_GROUP_NAME

# 获取队列信息
queue_name = get_svr_queue_name(0)
group_info = REDIS_CONN.queue_info(queue_name, SVR_CONSUMER_GROUP_NAME)

if group_info:
    print(f"Pending tasks: {group_info.get('pending', 0)}")
    print(f"Lag: {group_info.get('lag', 0)}")
    print(f"Consumers: {group_info.get('consumers', 0)}")
```

### 查看任务执行器状态

```python
from rag.utils.redis_conn import REDIS_CONN

# 获取所有task executor
executors = REDIS_CONN.smembers("TASKEXE")

for executor in executors:
    # 获取executor的心跳信息
    heartbeats = REDIS_CONN.zrange(executor, 0, -1)
    if heartbeats:
        import json
        latest = json.loads(heartbeats[-1])
        print(f"Executor: {latest['name']}")
        print(f"  Pending: {latest['pending']}")
        print(f"  Done: {latest['done']}")
        print(f"  Failed: {latest['failed']}")
        print(f"  Current: {latest['current']}")
```

---

## 注意事项

### ⚠️ 清理前的检查

1. **确认没有重要任务正在执行**
   - 检查当前正在处理的任务
   - 确认可以中断这些任务

2. **备份重要数据**
   - 如果不确定,先使用 `--dry-run` 预览
   - 考虑备份Redis数据

3. **停止task executor**
   - 清理大量任务时,建议先停止task executor
   - 避免清理过程中有新任务产生

### ⚠️ 清理后的操作

1. **重启服务**
   - 清理后建议重启task executor服务
   - 确保consumer group正确重建

2. **验证状态**
   - 检查队列是否已清空
   - 验证新任务能否正常执行

3. **重新提交任务**
   - 如果需要,在UI中重新解析文档
   - 或者重新触发知识图谱构建

---

## 故障排查

### 问题1: 清理后任务仍然存在

**可能原因**:
- Redis连接配置错误
- 队列名称不匹配
- 权限不足

**解决方法**:
```bash
# 检查Redis连接
docker exec -it ragflow-redis redis-cli ping

# 手动检查队列
docker exec -it ragflow-redis redis-cli XLEN rag_flow_svr_queue

# 检查配置文件
cat conf/service_conf.yaml | grep -A 5 redis
```

### 问题2: 清理后无法创建新任务

**可能原因**:
- Consumer group未正确重建
- Redis权限问题

**解决方法**:
```bash
# 重新创建consumer group
docker exec -it ragflow-redis redis-cli XGROUP CREATE rag_flow_svr_queue rag_flow_svr_task_broker 0 MKSTREAM

# 重启task executor
docker-compose restart ragflow-task-executor
```

### 问题3: 脚本执行失败

**可能原因**:
- Python环境问题
- 依赖包缺失
- 数据库连接失败

**解决方法**:
```bash
# 检查Python环境
python --version

# 安装依赖
pip install -r requirements.txt

# 检查数据库连接
python -c "from api.db import db; print(db.database)"
```

---

## 最佳实践

1. **定期监控队列状态**
   - 设置告警,当队列长度超过阈值时通知
   - 定期检查pending任务数量

2. **使用预览模式**
   - 清理前先使用 `--dry-run` 查看影响范围
   - 确认无误后再执行实际清理

3. **分批清理**
   - 对于大量任务,考虑分批清理
   - 避免一次性清理导致系统压力

4. **保留日志**
   - 清理操作的日志保存下来
   - 便于后续问题排查

5. **测试环境验证**
   - 在测试环境先验证清理脚本
   - 确认无问题后再在生产环境使用

---

## 相关文件

- `scripts/clear_task_queue.py` - 任务队列清理脚本
- `rag/utils/redis_conn.py` - Redis连接和队列操作
- `rag/settings.py` - 队列配置
- `api/db/services/task_service.py` - 任务服务
- `rag/svr/task_executor.py` - 任务执行器

---

## 参考资料

- [Redis Streams文档](https://redis.io/docs/data-types/streams/)
- [Redis XDEL命令](https://redis.io/commands/xdel/)
- [Redis XTRIM命令](https://redis.io/commands/xtrim/)
- [Redis XGROUP命令](https://redis.io/commands/xgroup/)

