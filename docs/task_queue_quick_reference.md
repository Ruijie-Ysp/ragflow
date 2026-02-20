# 任务队列清理 - 快速参考

## 🚀 快速开始

### 最常用的命令

```bash
# 1. 预览将要清理的内容(推荐第一步)
python scripts/clear_task_queue.py --all --dry-run

# 2. 清理所有任务
python scripts/clear_task_queue.py --all

# 3. 清理指定文档的任务
python scripts/clear_task_queue.py --doc-id <document_id>
```

---

## 📋 命令速查表

| 命令 | 说明 | 使用场景 |
|------|------|----------|
| `--all` | 清理所有任务(Redis+数据库) | 完全清空任务队列 |
| `--queue-only` | 只清理Redis队列 | 保留数据库记录 |
| `--db-only` | 只清理数据库 | 保留Redis队列 |
| `--doc-id <id>` | 清理指定文档 | 单个文档卡住 |
| `--dry-run` | 预览模式 | 查看影响范围 |

---

## 🔧 常见场景

### 场景1: 任务队列堵塞

```bash
# 停止服务
docker-compose stop ragflow-task-executor

# 清理队列
python scripts/clear_task_queue.py --all

# 重启服务
docker-compose start ragflow-task-executor
```

### 场景2: 文档处理卡住

```bash
# 清理该文档任务
python scripts/clear_task_queue.py --doc-id abc123

# 在UI重新解析文档
```

### 场景3: 测试环境清理

```bash
# 先预览
python scripts/clear_task_queue.py --all --dry-run

# 确认后清理
python scripts/clear_task_queue.py --all
```

---

## 🔍 队列监控

### 使用Redis CLI查看

```bash
# 进入Redis
docker exec -it ragflow-redis redis-cli

# 查看队列长度
XLEN rag_flow_svr_queue

# 查看队列信息
XINFO STREAM rag_flow_svr_queue

# 查看pending任务
XPENDING rag_flow_svr_queue rag_flow_svr_task_broker
```

### 使用Python查看

```python
from rag.utils.redis_conn import REDIS_CONN
from rag.settings import get_svr_queue_name, SVR_CONSUMER_GROUP_NAME

queue_name = get_svr_queue_name(0)
info = REDIS_CONN.queue_info(queue_name, SVR_CONSUMER_GROUP_NAME)
print(f"Pending: {info.get('pending', 0)}")
print(f"Lag: {info.get('lag', 0)}")
```

---

## ⚠️ 注意事项

### 清理前

- ✅ 确认没有重要任务正在执行
- ✅ 使用 `--dry-run` 预览影响
- ✅ 考虑停止task executor服务

### 清理后

- ✅ 重启task executor服务
- ✅ 验证队列已清空
- ✅ 测试新任务能否正常执行

---

## 🆘 故障排查

### 问题: 清理后任务仍存在

```bash
# 检查Redis连接
docker exec -it ragflow-redis redis-cli ping

# 手动查看队列
docker exec -it ragflow-redis redis-cli XLEN rag_flow_svr_queue

# 手动删除
docker exec -it ragflow-redis redis-cli DEL rag_flow_svr_queue
```

### 问题: 无法创建新任务

```bash
# 重建consumer group
docker exec -it ragflow-redis redis-cli \
  XGROUP CREATE rag_flow_svr_queue rag_flow_svr_task_broker 0 MKSTREAM

# 重启服务
docker-compose restart ragflow-task-executor
```

---

## 📚 更多信息

详细文档: `docs/task_queue_management.md`

脚本位置: `scripts/clear_task_queue.py`

---

## 💡 提示

1. **总是先用 `--dry-run` 预览**
2. **清理大量任务时先停止task executor**
3. **保留清理日志便于排查问题**
4. **定期监控队列状态,避免堆积**

