# RAGFlow 修改代码备份 - 使用指南

## 🎯 快速概览

此目录包含所有修改过的 RAGFlow 代码文件（15个），用于在 RAGFlow 更新版本后快速迁移修改。

---

## 📦 备份内容

### 文件统计
- **API 层**: 3 个文件
- **RAG 层**: 7 个文件
- **Agent 层**: 5 个文件
- **总计**: 15 个文件

### 主要修改
1. ✅ Langfuse 集成和跟踪
2. ✅ 详细的 token 使用统计
3. ✅ Agent ID 跟踪支持
4. ✅ 自定义标签和元数据

---

## 🔧 可用工具

### 1. 对比差异（推荐先使用）
```bash
cd docker/local_codes

# 快速对比
./compare_with_current.sh

# 详细对比（显示具体差异）
./compare_with_current.sh --verbose
```

**输出示例：**
```
✅ 相同: api/apps/langfuse_app.py
🔄 有差异: rag/llm/chat_model.py
   差异行数: 23
```

### 2. 恢复代码
```bash
cd docker/local_codes

# 恢复所有修改文件（会备份原文件）
./restore_codes.sh
```

**注意：** 
- 会自动备份原文件为 `.backup-YYYYMMDD-HHMMSS`
- 需要确认才会执行

### 3. 更新备份
```bash
# 在项目根目录运行
./backup_modified_codes.sh
```

---

## 🔄 版本更新工作流

### 场景 1: RAGFlow 小版本更新（推荐流程）

```bash
# 1. 更新 RAGFlow 代码
cd /path/to/ragflow
git pull origin main

# 2. 对比差异
cd docker/local_codes
./compare_with_current.sh

# 3a. 如果所有文件都相同 ✅
#     直接恢复即可
./restore_codes.sh

# 3b. 如果有差异 🔄
#     手动合并每个有差异的文件
#     使用 vimdiff 或 meld 等工具
vimdiff api/apps/langfuse_app.py ../../api/apps/langfuse_app.py

# 4. 重新构建镜像
cd ..
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .

# 5. 测试
docker-compose up -d
docker-compose logs -f ragflow

# 6. 更新备份
cd ..
./backup_modified_codes.sh
```

### 场景 2: RAGFlow 大版本更新（谨慎流程）

```bash
# 1. 备份当前环境
docker-compose down
cp -r . ../ragflow-backup

# 2. 更新代码
git fetch --tags
git checkout v2.0.0  # 假设新版本是 2.0.0

# 3. 详细对比差异
cd docker/local_codes
./compare_with_current.sh --verbose > diff_report.txt

# 4. 阅读差异报告
cat diff_report.txt

# 5. 逐个文件手动合并
#    使用三方合并工具
meld . ../..

# 6. 测试环境验证
cd ..
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:v2.0.0-custom .
docker-compose up -d

# 7. 充分测试后更新备份
cd ..
./backup_modified_codes.sh
```

### 场景 3: 紧急回滚

```bash
# 1. 停止服务
cd docker
docker-compose down

# 2. 回滚代码
git checkout previous-version

# 3. 恢复修改
cd local_codes
./restore_codes.sh

# 4. 重新构建和启动
cd ..
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .
docker-compose up -d
```

---

## 📝 手动合并指南

### 使用 vimdiff（命令行）

```bash
# 对比并合并单个文件
vimdiff docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# vimdiff 快捷键：
# ]c          - 跳到下一个差异
# [c          - 跳到上一个差异
# do          - 从另一个文件获取差异（diff obtain）
# dp          - 将差异推送到另一个文件（diff put）
# :diffupdate - 更新差异
# :wqa        - 保存所有文件并退出
```

### 使用 meld（图形化，推荐）

```bash
# 安装 meld（如果未安装）
# macOS:
brew install meld

# Ubuntu/Debian:
sudo apt install meld

# 对比单个文件
meld docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# 对比整个目录
meld docker/local_codes/ ./
```

### 使用 VS Code

```bash
# 对比单个文件
code --diff docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py
```

---

## ⚠️ 注意事项

### 1. 版本兼容性检查

在合并前，检查新版本的变化：

```bash
# 查看 CHANGELOG
cat CHANGELOG.md

# 查看特定文件的提交历史
git log --oneline api/apps/langfuse_app.py

# 查看具体变更
git show <commit-hash>
```

### 2. 测试清单

合并后必须测试：

- [ ] 服务正常启动
- [ ] Langfuse 集成正常
- [ ] Token 统计准确
- [ ] Agent 功能正常
- [ ] 日志无错误
- [ ] API 调用正常

### 3. 数据备份

更新前务必备份：

```bash
# 备份数据库
docker exec ragflow-mysql mysqldump -uroot -p${MYSQL_PASSWORD} rag_flow > backup.sql

# 备份 MinIO 数据
docker run --rm -v ragflow_minio_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/minio-backup.tar.gz /data

# 备份 Elasticsearch 数据（如果使用）
docker exec ragflow-es-01 \
  curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_1?wait_for_completion=true"
```

---

## 🔍 常见问题

### Q1: 如何知道哪些文件被修改了？

**A:** 查看 `FILE_LIST.txt` 或运行对比脚本：
```bash
./compare_with_current.sh
```

### Q2: 恢复脚本会覆盖我的文件吗？

**A:** 会，但会先备份原文件为 `.backup-YYYYMMDD-HHMMSS`，可以随时恢复。

### Q3: 如何只恢复部分文件？

**A:** 手动复制：
```bash
cp docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py
```

### Q4: 新版本的文件结构变了怎么办？

**A:** 需要手动调整：
1. 查看新版本的文件结构
2. 找到对应的新位置
3. 手动合并代码逻辑
4. 更新备份脚本中的文件路径

### Q5: 如何验证合并是否正确？

**A:** 
1. 运行单元测试（如果有）
2. 启动服务并查看日志
3. 测试关键功能
4. 对比 token 统计是否准确

---

## 📚 相关文档

- **README.md** - 详细的迁移指南和修改说明
- **FILE_LIST.txt** - 完整的文件清单
- **USAGE_GUIDE.md** - 本文件，使用指南

---

## 🎯 快速命令参考

```bash
# 对比差异
cd docker/local_codes && ./compare_with_current.sh

# 详细对比
cd docker/local_codes && ./compare_with_current.sh --verbose

# 恢复代码
cd docker/local_codes && ./restore_codes.sh

# 更新备份
./backup_modified_codes.sh

# 手动对比单个文件
vimdiff docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# 重新构建镜像
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .

# 启动服务
cd docker && docker-compose up -d

# 查看日志
docker-compose logs -f ragflow
```

---

## ✅ 最佳实践

1. **定期备份** - 每次修改代码后运行 `backup_modified_codes.sh`
2. **先对比再恢复** - 总是先运行 `compare_with_current.sh`
3. **测试环境验证** - 在测试环境先验证再部署到生产
4. **保留旧版本** - 更新前保留旧版本的 Docker 镜像
5. **文档记录** - 记录每次修改的原因和位置

---

**祝使用顺利！** 🚀

如有问题，请查看 `README.md` 或联系维护人员。

