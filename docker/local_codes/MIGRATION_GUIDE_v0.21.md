# RAGFlow v0.21.0 迁移实施指南

## 🎯 目标
将 v0.20.5 的个性化代码迁移到 v0.21.0，保留所有核心功能。

---

## 📋 前置条件

### 环境要求
- Docker 和 Docker Compose
- Git
- 文本编辑器（推荐 VS Code 或 vim）
- 差异对比工具（推荐 meld 或 vimdiff）

### 备份清单
```bash
# 1. 备份数据库
docker exec ragflow-mysql mysqldump -uroot -pinfini_rag_flow rag_flow > backup_$(date +%Y%m%d).sql

# 2. 备份 MinIO 数据
docker run --rm -v ragflow_minio_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data

# 3. 备份代码
cp -r docker docker.backup_$(date +%Y%m%d)
cp -r api api.backup_$(date +%Y%m%d)
cp -r rag rag.backup_$(date +%Y%m%d)
cp -r agent agent.backup_$(date +%Y%m%d)

# 4. 保存 Docker 镜像
docker save infiniflow/ragflow:nightly-slim > ragflow_v0.20.5.tar
```

---

## 🚀 迁移步骤

### 步骤 1: 环境准备

```bash
# 1.1 停止当前服务
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow/docker
docker-compose down

# 1.2 创建工作分支
cd ..
git checkout -b feature/migrate-v0.21

# 1.3 运行差异对比
cd docker/local_codes
./compare_with_current.sh > diff_report.txt
cat diff_report.txt
```

### 步骤 2: 验证 Agent ID 支持

```bash
# 2.1 检查 LLMBundle 构造函数
grep -A 20 "class LLMBundle" api/db/services/llm_service.py | grep "def __init__"

# 2.2 检查是否支持 agent_id 参数
grep -n "agent_id" api/db/services/llm_service.py
```

**预期结果**:
- 如果找到 `agent_id` 参数 → 继续步骤 3
- 如果未找到 → 跳转到"步骤 2.3: 添加 Agent ID 支持"

#### 步骤 2.3: 添加 Agent ID 支持（如果需要）

编辑 `api/db/services/llm_service.py`:

```python
class LLMBundle(LLM4Tenant):
    def __init__(self, tenant_id, llm_type, llm_name=None, lang="Chinese", agent_id=None, **kwargs):
        super().__init__(tenant_id, llm_type, llm_name, lang, **kwargs)
        self.agent_id = agent_id  # 添加这一行
        
        # 在 Langfuse 初始化时使用 agent_id
        langfuse_keys = TenantLangfuseService.filter_by_tenant(tenant_id=tenant_id)
        self.langfuse = None
        if langfuse_keys:
            langfuse = Langfuse(...)
            if langfuse.auth_check():
                self.langfuse = langfuse
                # 将 agent_id 添加到 metadata
                self.langfuse_metadata = {"agent_id": agent_id} if agent_id else {}
```

### 步骤 3: 迁移低风险文件

```bash
# 3.1 复制无差异文件
cp docker/local_codes/rag/prompts/template.py rag/prompts/template.py

# 3.2 复制小差异文件（建议使用旧版本）
cp docker/local_codes/api/apps/langfuse_app.py api/apps/langfuse_app.py
cp docker/local_codes/agent/component/categorize.py agent/component/categorize.py

# 3.3 验证语法
python3 -m py_compile api/apps/langfuse_app.py
python3 -m py_compile agent/component/categorize.py
```

### 步骤 4: 迁移 Agent 组件

#### 4.1 agent/component/llm.py

```bash
# 使用 vimdiff 对比
vimdiff docker/local_codes/agent/component/llm.py agent/component/llm.py
```

**关键修改点**:
1. 在 `__init__` 中添加 `agent_id` 参数传递
2. 保留新版本的 `_sys_prompt_and_msg` 方法
3. 合并两者的优点

**建议修改**:
```python
# 在 __init__ 中
self.chat_mdl = LLMBundle(
    self._canvas.get_tenant_id(), 
    TenantLLMService.llm_id2llm_type(self._param.llm_id),
    self._param.llm_id, 
    max_retries=self._param.max_retries,
    retry_interval=self._param.delay_after_error,
    agent_id=self._canvas.get_agent_id()  # 添加这一行
)
```

#### 4.2 agent/component/agent_with_tools.py

```bash
vimdiff docker/local_codes/agent/component/agent_with_tools.py agent/component/agent_with_tools.py
```

**关键修改**: 同样添加 `agent_id` 参数

#### 4.3 agent/tools/retrieval.py

```bash
vimdiff docker/local_codes/agent/tools/retrieval.py agent/tools/retrieval.py
```

**关键修改**: 在创建 LLMBundle 时添加 `agent_id`

#### 4.4 agent/canvas.py

```bash
# 差异较小，可以直接复制或手动合并
vimdiff docker/local_codes/agent/canvas.py agent/canvas.py
```

### 步骤 5: 处理 Chunker → Splitter 迁移

```bash
# 5.1 查看旧版本的修改
cat docker/local_codes/rag/flow/chunker/chunker.py

# 5.2 查看新版本的 splitter
cat rag/flow/splitter/splitter.py

# 5.3 分析差异
# 注意: chunker.py 中的 agent_id 相关修改需要迁移到 splitter.py
```

**迁移策略**:
1. 找到 chunker.py 中所有涉及 `agent_id` 的代码
2. 在 splitter.py 的对应位置添加相同逻辑
3. 确保 LLMBundle 调用时传递 `agent_id`

**示例**:
```python
# 在 splitter.py 中找到 LLMBundle 的创建位置
# 添加 agent_id 参数
chat_mdl = LLMBundle(
    tenant_id, 
    LLMType.CHAT,
    agent_id=getattr(self, 'agent_id', None)  # 添加这一行
)
```

### 步骤 6: 迁移大文件（需要仔细合并）

#### 6.1 api/db/services/llm_service.py

```bash
# 使用 meld 进行三方合并（推荐）
meld docker/local_codes/api/db/services/llm_service.py api/db/services/llm_service.py
```

**合并要点**:
1. 保留新版本的基础结构和优化
2. 添加旧版本的 Langfuse 集成代码
3. 确保 `agent_id` 参数在所有相关方法中传递
4. 保留旧版本的详细 token 统计

**关键区域**:
- `LLMBundle.__init__` - 添加 agent_id 支持
- `encode`, `encode_queries` - 保留 Langfuse 跟踪
- `chat` - 保留详细的 token 统计和 Langfuse 集成

#### 6.2 api/db/services/tenant_llm_service.py

```bash
meld docker/local_codes/api/db/services/tenant_llm_service.py api/db/services/tenant_llm_service.py
```

**合并要点**:
1. 保留旧版本的 `trace_id`, `ragflow_api_key`, `langfuse_public_key` 字段
2. 检查新版本是否有重要的 bug 修复
3. 合并两者的优点

#### 6.3 rag/llm/chat_model.py

```bash
meld docker/local_codes/rag/llm/chat_model.py rag/llm/chat_model.py
```

**合并要点**:
1. 保留详细的 token 统计逻辑
2. 确保支持多种 LLM 提供商的 token 格式
3. 保留新版本的性能优化

#### 6.4 rag/utils/__init__.py

```bash
meld docker/local_codes/rag/utils/__init__.py rag/utils/__init__.py
```

**合并要点**:
1. 保留详细的 token 提取函数
2. 支持 `prompt_tokens`, `completion_tokens`, `total_tokens`

#### 6.5 rag/prompts/generator.py

```bash
meld docker/local_codes/rag/prompts/generator.py rag/prompts/generator.py
```

**合并要点**:
1. 保留新版本的 prompt 优化
2. 添加旧版本的自定义 prompt 功能

#### 6.6 rag/flow/parser/parser.py

```bash
meld docker/local_codes/rag/flow/parser/parser.py rag/flow/parser/parser.py
```

**合并要点**:
1. 添加 agent_id 支持
2. 保留新版本的解析优化

#### 6.7 rag/flow/tokenizer/tokenizer.py

```bash
meld docker/local_codes/rag/flow/tokenizer/tokenizer.py rag/flow/tokenizer/tokenizer.py
```

**合并要点**:
1. 添加 agent_id 支持
2. 保留新版本的分词优化

### 步骤 7: 部署 OpenAI 代理服务

```bash
# 7.1 复制代理服务文件
cp docker/local_codes/ragflow_openai_proxy.py ./
cp docker/local_codes/requirements_proxy.txt ./
cp docker/local_codes/docker/Dockerfile.proxy docker/

# 7.2 更新 docker-compose.yml
# 参考 docker/local_codes/docker-compose-v-local-codes.yml
```

#### 7.2.1 编辑 docker/docker-compose.yml

添加以下内容:

```yaml
services:
  ragflow:
    # ... 现有配置 ...
    volumes:
      # ... 现有 volumes ...
      # 添加修改文件的挂载
      - ../api/apps/langfuse_app.py:/ragflow/api/apps/langfuse_app.py
      - ../api/db/services/llm_service.py:/ragflow/api/db/services/llm_service.py
      - ../api/db/services/tenant_llm_service.py:/ragflow/api/db/services/tenant_llm_service.py
      - ../rag/llm/chat_model.py:/ragflow/rag/llm/chat_model.py
      - ../rag/utils/__init__.py:/ragflow/rag/utils/__init__.py
      - ../agent/canvas.py:/ragflow/agent/canvas.py
      - ../agent/component/llm.py:/ragflow/agent/component/llm.py
      - ../agent/component/categorize.py:/ragflow/agent/component/categorize.py
      - ../agent/component/agent_with_tools.py:/ragflow/agent/component/agent_with_tools.py
      - ../agent/tools/retrieval.py:/ragflow/agent/tools/retrieval.py
      - ../rag/prompts/generator.py:/ragflow/rag/prompts/generator.py
      - ../rag/prompts/template.py:/ragflow/rag/prompts/template.py
      - ../rag/flow/parser/parser.py:/ragflow/rag/flow/parser/parser.py
      - ../rag/flow/splitter/splitter.py:/ragflow/rag/flow/splitter/splitter.py
      - ../rag/flow/tokenizer/tokenizer.py:/ragflow/rag/flow/tokenizer/tokenizer.py
    environment:
      # ... 现有环境变量 ...
      - OTEL_SDK_DISABLED=${OTEL_SDK_DISABLED:-false}

  ragflow-proxy:
    build:
      context: ..
      dockerfile: docker/Dockerfile.proxy
    image: ragflow-openai-proxy:latest
    container_name: ragflow-openai-proxy
    depends_on:
      ragflow:
        condition: service_started
    ports:
      - ${PROXY_PORT:-10101}:8000
    env_file: .env
    environment:
      - RAGFLOW_BASE_URL=http://ragflow:80
      - RAGFLOW_API_KEY=${RAGFLOW_API_KEY}
      - TZ=${TIMEZONE}
    networks:
      - ragflow
    restart: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

#### 7.2.2 更新 docker/.env

添加以下配置:

```bash
# OpenTelemetry Configuration
OTEL_SDK_DISABLED=false

# RAGFlow OpenAI Proxy Configuration
RAGFLOW_API_KEY=ragflow-YOUR_API_KEY_HERE
PROXY_PORT=10101
```

### 步骤 8: 测试验证

```bash
# 8.1 构建镜像（如果需要）
# docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:v0.21.0-custom .

# 8.2 启动服务
cd docker
docker-compose up -d

# 8.3 查看日志
docker-compose logs -f ragflow
docker-compose logs -f ragflow-proxy

# 8.4 等待服务启动
sleep 30
```

#### 8.4.1 测试 Langfuse 集成

```bash
# 测试 Langfuse API
curl -X GET http://localhost:9380/api/langfuse/api_key \
  -H "Authorization: Bearer YOUR_RAGFLOW_TOKEN"
```

#### 8.4.2 测试 Agent 功能

```bash
# 测试 Agent API
curl -X POST http://localhost:9380/api/v1/agents/YOUR_AGENT_ID/chat \
  -H "Authorization: Bearer YOUR_RAGFLOW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

#### 8.4.3 测试 OpenAI 代理

```bash
# 测试健康检查
curl http://localhost:10101/health

# 测试 OpenAI 兼容 API
curl -X POST http://localhost:10101/v1/chat/completions \
  -H "Authorization: Bearer YOUR_AGENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

#### 8.4.4 检查日志错误

```bash
# 检查是否有错误
docker-compose logs ragflow | grep -i error
docker-compose logs ragflow | grep -i exception

# 检查 Langfuse 连接
docker-compose logs ragflow | grep -i langfuse
```

### 步骤 9: 性能和功能验证

#### 9.1 Token 统计验证

1. 在 Langfuse 界面查看 trace
2. 验证是否有详细的 token 统计（prompt_tokens, completion_tokens, total_tokens）
3. 验证 agent_id 是否正确记录

#### 9.2 Agent ID 跟踪验证

1. 创建一个 Agent
2. 通过 Agent API 发送请求
3. 在 Langfuse 中查看 trace，确认 agent_id 正确传递

#### 9.3 性能测试

```bash
# 简单的性能测试
time curl -X POST http://localhost:9380/api/v1/agents/YOUR_AGENT_ID/chat \
  -H "Authorization: Bearer YOUR_RAGFLOW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### 步骤 10: 更新备份

```bash
# 10.1 运行备份脚本（如果有）
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow
# ./backup_modified_codes.sh

# 10.2 手动更新备份
cd docker/local_codes
# 更新 FILE_LIST.txt 中的时间戳
# 更新 README.md 中的版本信息
```

---

## 🔧 故障排查

### 问题 1: 服务启动失败

**症状**: `docker-compose up -d` 后服务无法启动

**排查步骤**:
```bash
# 查看详细日志
docker-compose logs ragflow

# 检查语法错误
docker exec -it ragflow-server python3 -m py_compile /ragflow/api/apps/langfuse_app.py
```

**常见原因**:
- Python 语法错误
- 缺少依赖
- 文件路径错误

### 问题 2: Langfuse 连接失败

**症状**: 日志中出现 "Cannot connect to Langfuse"

**排查步骤**:
```bash
# 检查 Langfuse 配置
docker exec -it ragflow-server env | grep LANGFUSE

# 测试网络连接
docker exec -it ragflow-server curl -v http://host.docker.internal:3000
```

**解决方案**:
- 确保 Langfuse 服务正在运行
- 检查 host.docker.internal 是否可访问
- 验证 Langfuse 凭据

### 问题 3: Agent ID 未传递

**症状**: Langfuse 中看不到 agent_id

**排查步骤**:
```bash
# 检查 LLMBundle 是否支持 agent_id
grep -n "agent_id" api/db/services/llm_service.py

# 检查 agent 组件是否传递 agent_id
grep -n "agent_id" agent/component/llm.py
```

**解决方案**:
- 确保 LLMBundle 构造函数接受 agent_id 参数
- 确保所有 agent 组件都传递 agent_id

### 问题 4: OpenAI 代理无法访问

**症状**: curl http://localhost:10101/health 失败

**排查步骤**:
```bash
# 检查代理服务状态
docker-compose ps ragflow-proxy

# 查看代理日志
docker-compose logs ragflow-proxy

# 检查端口映射
docker port ragflow-openai-proxy
```

---

## ✅ 验收标准

### 功能验收
- [ ] RAGFlow 服务正常启动
- [ ] Langfuse 集成正常工作
- [ ] Agent 功能正常
- [ ] Token 统计准确且详细
- [ ] Agent ID 正确跟踪
- [ ] OpenAI 代理服务正常
- [ ] 所有 API 端点响应正常

### 性能验收
- [ ] 响应时间无明显增加
- [ ] 内存使用正常
- [ ] CPU 使用正常
- [ ] 无内存泄漏

### 质量验收
- [ ] 日志无错误
- [ ] 日志无警告（或警告可解释）
- [ ] 代码通过语法检查
- [ ] 所有测试通过

---

## 📚 参考文档

- [迁移分析报告](./MIGRATION_ANALYSIS_v0.21.md)
- [README](./README.md)
- [使用指南](./USAGE_GUIDE.md)
- [快速参考](./QUICK_REFERENCE.md)

---

**最后更新**: 2025-10-23  
**维护者**: RAGFlow 团队

