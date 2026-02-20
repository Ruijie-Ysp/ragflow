# RAGFlow 修改代码备份

## 📋 备份说明

此目录包含所有修改过的 RAGFlow 代码文件，用于在 RAGFlow 更新版本后迁移修改。

## 📦 备份文件列表

### API 层（3个文件）
```
api/apps/langfuse_app.py                    # Langfuse 集成
api/db/services/llm_service.py              # LLM 服务
api/db/services/tenant_llm_service.py       # 租户 LLM 服务（支持自定义标签和元数据）
```

### RAG 层（7个文件）

#### LLM
```
rag/llm/chat_model.py                       # 聊天模型（支持详细的 token 使用统计）
```

#### Utils
```
rag/utils/__init__.py                       # 工具函数（支持详细的 token 使用提取）
```

#### Prompts
```
rag/prompts/generator.py                    # Prompt 生成器
rag/prompts/template.py                     # Prompt 模板
```

#### Flow
```
rag/flow/parser/parser.py                   # 解析器（支持 agent_id 跟踪）
rag/flow/chunker/chunker.py                 # 分块器（支持 agent_id 跟踪）
rag/flow/tokenizer/tokenizer.py             # 分词器（支持 agent_id 跟踪）
```

### Agent 层（5个文件）
```
agent/canvas.py                             # Agent 画布（支持 agent_id 跟踪）
agent/component/llm.py                      # LLM 组件
agent/component/categorize.py               # 分类组件
agent/component/agent_with_tools.py         # 带工具的 Agent
agent/tools/retrieval.py                    # 检索工具
```

### Proxy 服务（3个文件）
```
ragflow_openai_proxy.py                     # RAGFlow OpenAI 代理服务器（新增）
requirements_proxy.txt                      # Proxy 服务依赖（新增）
docker/Dockerfile.proxy                     # Proxy 服务 Dockerfile（新增）
```

**说明**：Proxy 服务将 RAGFlow Agent API 转换为标准 OpenAI API 格式，使用 agent_id 作为 API Key。

## 🔄 版本更新迁移步骤

### 1. 更新 RAGFlow 到新版本

```bash
# 拉取最新代码
git pull origin main

# 或者下载新版本
wget https://github.com/infiniflow/ragflow/archive/refs/tags/vX.X.X.tar.gz
tar -xzf vX.X.X.tar.gz
```

### 2. 对比修改

使用 diff 工具对比备份文件和新版本文件的差异：

```bash
# 对比单个文件
diff docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# 对比整个目录
diff -r docker/local_codes/ ./ --exclude=docker
```

### 3. 合并修改

根据对比结果，有以下几种处理方式：

#### 方式 A：新版本文件未变化
如果新版本的文件与旧版本相同，直接复制备份文件：

```bash
cp docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py
```

#### 方式 B：新版本文件有变化
如果新版本的文件有变化，需要手动合并：

1. 使用三方合并工具（推荐）：
```bash
# 使用 meld（图形化工具）
meld docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# 使用 vimdiff
vimdiff docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py
```

2. 或者使用 git merge：
```bash
# 创建临时分支
git checkout -b merge-custom-changes

# 将备份文件复制到新版本
cp docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py

# 查看差异并手动解决冲突
git diff
```

#### 方式 C：批量复制（谨慎使用）
如果确认新版本没有重大变化，可以批量复制：

```bash
# 备份当前版本（以防万一）
cp -r api api.backup
cp -r rag rag.backup
cp -r agent agent.backup

# 批量复制修改文件
cp -r docker/local_codes/api/* api/
cp -r docker/local_codes/rag/* rag/
cp -r docker/local_codes/agent/* agent/
```

### 4. 测试验证

```bash
# 重新构建镜像
docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .

# 启动服务
cd docker
docker-compose up -d

# 查看日志
docker-compose logs -f ragflow

# 测试功能
# - 测试 Langfuse 集成
# - 测试 Agent 功能
# - 测试 token 统计
```

### 5. 更新备份

如果在新版本上又做了修改，记得更新备份：

```bash
# 运行备份脚本
./backup_modified_codes.sh
```

## 📝 修改说明

### 主要修改内容

1. **Langfuse 集成**
   - 添加了 Langfuse 跟踪支持
   - 支持 agent_id 跟踪
   - 支持详细的 token 使用统计

2. **Token 统计增强**
   - 详细的 token 使用统计（prompt_tokens, completion_tokens, total_tokens）
   - 支持多种 LLM 提供商的 token 统计

3. **自定义标签和元数据**
   - 租户 LLM 服务支持自定义标签
   - 支持元数据存储和查询

4. **Agent 增强**
   - Agent 组件支持 agent_id 跟踪
   - 改进的工具调用和检索功能

## ⚠️ 注意事项

1. **版本兼容性**
   - 在迁移前，请仔细阅读新版本的 CHANGELOG
   - 检查是否有 API 变更或不兼容的修改

2. **测试充分性**
   - 迁移后务必进行充分测试
   - 特别是 Langfuse 集成和 Agent 功能

3. **备份数据**
   - 在更新前备份数据库和对象存储
   - 保留旧版本的 Docker 镜像

4. **逐步迁移**
   - 建议先在测试环境验证
   - 确认无误后再部署到生产环境

## 🔍 快速检查清单

迁移前检查：
- [ ] 已备份当前数据库
- [ ] 已备份对象存储数据
- [ ] 已保留旧版本 Docker 镜像
- [ ] 已阅读新版本 CHANGELOG
- [ ] 已对比所有修改文件的差异

迁移后检查：
- [ ] 所有服务正常启动
- [ ] Langfuse 集成正常工作
- [ ] Agent 功能正常
- [ ] Token 统计准确
- [ ] 日志中无错误信息
- [ ] 已更新备份文件

## 📚 相关文档

- [RAGFlow 官方文档](https://ragflow.io/docs)
- [Langfuse 文档](https://langfuse.com/docs)
- [Git 合并冲突解决](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)

---

**备份时间**: 自动生成
**备份脚本**: `backup_modified_codes.sh`
