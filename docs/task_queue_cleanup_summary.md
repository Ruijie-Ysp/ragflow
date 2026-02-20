# 任务队列清理工具 - 完成总结

## 📦 新增文件

为了方便清理RAGFlow的任务队列,我创建了以下文件:

### 1. 核心脚本

**`scripts/clear_task_queue.py`** - 任务队列清理脚本
- 功能完整的Python脚本
- 支持清理Redis队列和数据库任务
- 提供预览模式和多种清理选项
- 包含详细的日志输出

### 2. 文档

**`docs/task_queue_management.md`** - 完整管理指南
- 任务队列架构说明
- 三种清理方法详解
- 常见场景处理
- 监控和故障排查

**`docs/task_queue_quick_reference.md`** - 快速参考卡片
- 常用命令速查
- 场景化示例
- 故障排查要点

**`docs/task_queue_cleanup_summary.md`** - 本文档
- 新增文件说明
- 使用示例
- 注意事项

### 3. 辅助文件

**`scripts/README.md`** - 脚本目录说明
- 脚本列表和用途
- 使用说明
- 开发规范

**`scripts/test_clear_queue.sh`** - 测试脚本
- 验证环境配置
- 测试脚本功能

---

## 🚀 快速开始

### 最简单的使用方式

```bash
# 1. 进入项目目录
cd /path/to/ragflow

# 2. 预览将要清理的内容(推荐)
python scripts/clear_task_queue.py --all --dry-run

# 3. 确认后执行清理
python scripts/clear_task_queue.py --all
```

### 清理指定文档的任务

```bash
# 获取文档ID(从UI或数据库)
# 然后执行清理
python scripts/clear_task_queue.py --doc-id <your_document_id>
```

---

## 📋 功能特性

### ✅ 支持的清理操作

1. **Redis队列清理**
   - 清空任务消息
   - 重建consumer group
   - 清理取消标记

2. **数据库清理**
   - 删除任务记录
   - 重置文档状态
   - 支持按文档ID过滤

3. **灵活的选项**
   - `--all`: 清理所有(Redis + 数据库)
   - `--queue-only`: 只清理Redis
   - `--db-only`: 只清理数据库
   - `--doc-id`: 指定文档
   - `--dry-run`: 预览模式

### ✅ 安全特性

- **预览模式**: 先查看影响范围
- **详细日志**: 记录每个操作
- **错误处理**: 捕获并报告异常
- **分步执行**: 可以分别清理不同部分

---

## 💡 使用场景

### 场景1: 任务队列堵塞

**症状**: 
- 文档一直显示"处理中"
- 队列长度持续增长
- 新任务无法执行

**解决方案**:
```bash
# 1. 停止task executor
docker-compose stop ragflow-task-executor

# 2. 清理队列
python scripts/clear_task_queue.py --all

# 3. 重启服务
docker-compose start ragflow-task-executor
```

### 场景2: 单个文档卡住

**症状**:
- 某个文档处理进度卡住
- 其他文档正常

**解决方案**:
```bash
# 清理该文档的任务
python scripts/clear_task_queue.py --doc-id abc123

# 在UI中重新解析该文档
```

### 场景3: 开发/测试环境清理

**症状**:
- 测试产生大量任务
- 需要清空重新开始

**解决方案**:
```bash
# 预览
python scripts/clear_task_queue.py --all --dry-run

# 清理
python scripts/clear_task_queue.py --all
```

### 场景4: 只清理Redis,保留记录

**症状**:
- Redis队列有问题
- 但想保留数据库记录

**解决方案**:
```bash
python scripts/clear_task_queue.py --queue-only
```

---

## 🔍 监控队列状态

### 方法1: 使用脚本查看

```python
from rag.utils.redis_conn import REDIS_CONN
from rag.settings import get_svr_queue_name, SVR_CONSUMER_GROUP_NAME

# 查看队列信息
queue_name = get_svr_queue_name(0)
info = REDIS_CONN.queue_info(queue_name, SVR_CONSUMER_GROUP_NAME)

if info:
    print(f"Pending tasks: {info.get('pending', 0)}")
    print(f"Lag: {info.get('lag', 0)}")
    print(f"Consumers: {info.get('consumers', 0)}")
```

### 方法2: 使用Redis CLI

```bash
# 进入Redis
docker exec -it ragflow-redis redis-cli

# 查看队列长度
XLEN rag_flow_svr_queue

# 查看详细信息
XINFO STREAM rag_flow_svr_queue

# 查看pending任务
XPENDING rag_flow_svr_queue rag_flow_svr_task_broker
```

---

## ⚠️ 重要注意事项

### 清理前

1. **确认影响范围**
   - 使用 `--dry-run` 预览
   - 了解将要删除的任务数量

2. **备份重要数据**
   - 如果不确定,先备份Redis
   - 考虑备份数据库

3. **停止相关服务**
   - 清理大量任务时停止task executor
   - 避免清理过程中产生新任务

### 清理后

1. **重启服务**
   - 重启task executor服务
   - 确保consumer group正确重建

2. **验证状态**
   - 检查队列是否清空
   - 测试新任务能否正常执行

3. **重新提交任务**
   - 在UI中重新解析需要的文档
   - 或重新触发相关操作

---

## 🐛 故障排查

### 问题1: 脚本执行失败

**错误信息**: `ModuleNotFoundError` 或 `ImportError`

**解决方法**:
```bash
# 检查Python环境
python --version

# 确保在项目根目录
cd /path/to/ragflow

# 安装依赖
pip install -r requirements.txt
```

### 问题2: Redis连接失败

**错误信息**: `Connection refused` 或 `Redis can't be connected`

**解决方法**:
```bash
# 检查Redis服务
docker ps | grep redis

# 检查配置
cat conf/service_conf.yaml | grep -A 5 redis

# 测试连接
docker exec -it ragflow-redis redis-cli ping
```

### 问题3: 数据库连接失败

**错误信息**: `Can't connect to MySQL server`

**解决方法**:
```bash
# 检查MySQL服务
docker ps | grep mysql

# 检查配置
cat conf/service_conf.yaml | grep -A 5 mysql

# 测试连接
docker exec -it ragflow-mysql mysql -u root -p
```

### 问题4: 清理后任务仍存在

**可能原因**: 
- 队列名称不匹配
- 权限不足
- 配置错误

**解决方法**:
```bash
# 手动检查队列
docker exec -it ragflow-redis redis-cli XLEN rag_flow_svr_queue

# 手动删除
docker exec -it ragflow-redis redis-cli DEL rag_flow_svr_queue

# 重建consumer group
docker exec -it ragflow-redis redis-cli \
  XGROUP CREATE rag_flow_svr_queue rag_flow_svr_task_broker 0 MKSTREAM
```

---

## 📚 相关文档

- **完整指南**: [docs/task_queue_management.md](task_queue_management.md)
- **快速参考**: [docs/task_queue_quick_reference.md](task_queue_quick_reference.md)
- **脚本说明**: [scripts/README.md](../scripts/README.md)

---

## 🔗 相关代码文件

- `scripts/clear_task_queue.py` - 清理脚本
- `rag/utils/redis_conn.py` - Redis连接和队列操作
- `rag/settings.py` - 队列配置
- `api/db/services/task_service.py` - 任务服务
- `rag/svr/task_executor.py` - 任务执行器

---

## 📝 命令参考

### 完整命令格式

```bash
python scripts/clear_task_queue.py [选项]

选项:
  --queue-only        只清理Redis队列,不清理数据库
  --db-only          只清理数据库任务记录,不清理Redis队列
  --doc-id DOC_ID    只清理指定文档的任务
  --all              清理所有任务(默认)
  --dry-run          预览将要清理的内容,不实际执行
  -h, --help         显示帮助信息
```

### 常用命令示例

```bash
# 查看帮助
python scripts/clear_task_queue.py --help

# 预览所有任务
python scripts/clear_task_queue.py --all --dry-run

# 清理所有任务
python scripts/clear_task_queue.py --all

# 只清理Redis
python scripts/clear_task_queue.py --queue-only

# 只清理数据库
python scripts/clear_task_queue.py --db-only

# 清理指定文档
python scripts/clear_task_queue.py --doc-id abc123

# 预览指定文档
python scripts/clear_task_queue.py --doc-id abc123 --dry-run
```

---

## ✅ 最佳实践

1. **总是先预览**
   - 使用 `--dry-run` 查看影响
   - 确认无误后再执行

2. **定期监控**
   - 监控队列长度
   - 设置告警阈值

3. **分批清理**
   - 大量任务分批处理
   - 避免系统压力过大

4. **保留日志**
   - 保存清理操作日志
   - 便于问题排查

5. **测试验证**
   - 在测试环境先验证
   - 确认无问题后用于生产

---

## 🎯 总结

通过这套工具,你可以:

✅ **快速清理**任务队列
✅ **灵活选择**清理范围
✅ **安全预览**操作影响
✅ **详细日志**记录过程
✅ **故障排查**问题定位

如有任何问题,请参考详细文档或提交Issue。

