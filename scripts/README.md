# RAGFlow 脚本工具

本目录包含RAGFlow的各种管理和维护脚本。

## 📁 脚本列表

### clear_task_queue.py

**功能**: 清理RAGFlow任务队列

**用途**:
- 清理Redis Stream任务队列
- 清理数据库任务记录
- 清理任务取消标记
- 重置文档处理状态

**快速使用**:
```bash
# 预览将要清理的内容
python scripts/clear_task_queue.py --all --dry-run

# 清理所有任务
python scripts/clear_task_queue.py --all

# 清理指定文档的任务
python scripts/clear_task_queue.py --doc-id <document_id>
```

**详细文档**:
- 完整指南: [docs/task_queue_management.md](../docs/task_queue_management.md)
- 快速参考: [docs/task_queue_quick_reference.md](../docs/task_queue_quick_reference.md)

---

## 📖 使用说明

### 环境要求

- Python 3.8+
- 已安装RAGFlow依赖包
- 可访问Redis和MySQL数据库

### 通用步骤

1. **进入项目目录**
   ```bash
   cd /path/to/ragflow
   ```

2. **激活虚拟环境**(如果使用)
   ```bash
   source venv/bin/activate
   ```

3. **运行脚本**
   ```bash
   python scripts/<script_name>.py [options]
   ```

---

## 🔧 常见问题

### Q: 脚本执行失败怎么办?

A: 检查以下几点:
1. Python环境是否正确
2. 依赖包是否已安装
3. 数据库连接是否正常
4. Redis服务是否运行

### Q: 如何查看脚本帮助信息?

A: 使用 `-h` 或 `--help` 参数:
```bash
python scripts/clear_task_queue.py --help
```

### Q: 脚本是否安全?

A: 
- 所有脚本都支持 `--dry-run` 预览模式
- 建议先在测试环境验证
- 重要操作前建议备份数据

---

## 📝 开发新脚本

如果需要添加新的管理脚本,请遵循以下规范:

1. **命名规范**: 使用小写字母和下划线,如 `clear_task_queue.py`

2. **文档要求**:
   - 脚本开头添加docstring说明功能和用法
   - 在本README中添加脚本说明
   - 如果复杂,创建独立的文档文件

3. **参数规范**:
   - 使用 `argparse` 处理命令行参数
   - 提供 `--help` 帮助信息
   - 支持 `--dry-run` 预览模式(如果适用)

4. **日志规范**:
   - 使用 `logging` 模块记录日志
   - 区分INFO、WARNING、ERROR级别
   - 提供清晰的进度和结果信息

5. **错误处理**:
   - 捕获并处理可能的异常
   - 提供有用的错误信息
   - 适当的退出码(0=成功, 非0=失败)

---

## 🤝 贡献

欢迎贡献新的脚本工具!请确保:

1. 代码符合项目规范
2. 添加完整的文档
3. 经过充分测试
4. 更新本README

---

## 📞 支持

如有问题,请:
1. 查看相关文档
2. 检查常见问题
3. 提交Issue到GitHub仓库

