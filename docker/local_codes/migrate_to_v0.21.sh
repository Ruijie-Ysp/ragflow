#!/bin/bash

# RAGFlow v0.21.0 自动迁移脚本
# 用途：自动化迁移低风险文件和配置

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAGFlow v0.21.0 自动迁移脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "${PROJECT_ROOT}/docker/docker-compose.yml" ]; then
    echo -e "${RED}❌ 错误: 未找到 docker-compose.yml${NC}"
    echo -e "${RED}   请确保在 RAGFlow 项目根目录运行此脚本${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 项目根目录: ${PROJECT_ROOT}${NC}"
echo ""

# 询问是否继续
read -p "$(echo -e ${YELLOW}是否继续迁移？这将修改项目文件。[y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}迁移已取消${NC}"
    exit 0
fi

# 步骤 1: 创建备份
echo -e "${BLUE}步骤 1: 创建备份...${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${PROJECT_ROOT}/backup_${BACKUP_DATE}"

mkdir -p "${BACKUP_DIR}"
cp -r "${PROJECT_ROOT}/api" "${BACKUP_DIR}/"
cp -r "${PROJECT_ROOT}/rag" "${BACKUP_DIR}/"
cp -r "${PROJECT_ROOT}/agent" "${BACKUP_DIR}/"
cp -r "${PROJECT_ROOT}/docker" "${BACKUP_DIR}/"

echo -e "${GREEN}✓ 备份已创建: ${BACKUP_DIR}${NC}"
echo ""

# 步骤 2: 运行差异对比
echo -e "${BLUE}步骤 2: 运行差异对比...${NC}"
cd "${SCRIPT_DIR}"
./compare_with_current.sh > "${BACKUP_DIR}/diff_report.txt"
cat "${BACKUP_DIR}/diff_report.txt"
echo -e "${GREEN}✓ 差异报告已保存: ${BACKUP_DIR}/diff_report.txt${NC}"
echo ""

# 步骤 3: 迁移低风险文件
echo -e "${BLUE}步骤 3: 迁移低风险文件...${NC}"

# 3.1 无差异文件
echo -e "${YELLOW}3.1 复制无差异文件...${NC}"
if diff -q "${SCRIPT_DIR}/rag/prompts/template.py" "${PROJECT_ROOT}/rag/prompts/template.py" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ rag/prompts/template.py 无差异，跳过${NC}"
else
    cp "${SCRIPT_DIR}/rag/prompts/template.py" "${PROJECT_ROOT}/rag/prompts/template.py"
    echo -e "${GREEN}  ✓ 已复制 rag/prompts/template.py${NC}"
fi

# 3.2 小差异文件（使用旧版本）
echo -e "${YELLOW}3.2 复制小差异文件（使用增强版本）...${NC}"

# api/apps/langfuse_app.py - 旧版本有更好的错误处理
cp "${SCRIPT_DIR}/api/apps/langfuse_app.py" "${PROJECT_ROOT}/api/apps/langfuse_app.py"
echo -e "${GREEN}  ✓ 已复制 api/apps/langfuse_app.py (增强的错误处理)${NC}"

# agent/component/categorize.py - 仅 2 行差异
cp "${SCRIPT_DIR}/agent/component/categorize.py" "${PROJECT_ROOT}/agent/component/categorize.py"
echo -e "${GREEN}  ✓ 已复制 agent/component/categorize.py${NC}"

echo ""

# 步骤 4: 检查 Agent ID 支持
echo -e "${BLUE}步骤 4: 检查 Agent ID 支持...${NC}"
if grep -q "agent_id" "${PROJECT_ROOT}/api/db/services/llm_service.py"; then
    echo -e "${GREEN}✓ LLMBundle 已支持 agent_id 参数${NC}"
    AGENT_ID_SUPPORTED=true
else
    echo -e "${YELLOW}⚠️  LLMBundle 不支持 agent_id 参数${NC}"
    echo -e "${YELLOW}   需要手动添加 agent_id 支持${NC}"
    AGENT_ID_SUPPORTED=false
fi
echo ""

# 步骤 5: 复制 OpenAI 代理服务文件
echo -e "${BLUE}步骤 5: 部署 OpenAI 代理服务...${NC}"

cp "${SCRIPT_DIR}/ragflow_openai_proxy.py" "${PROJECT_ROOT}/"
echo -e "${GREEN}  ✓ 已复制 ragflow_openai_proxy.py${NC}"

cp "${SCRIPT_DIR}/requirements_proxy.txt" "${PROJECT_ROOT}/"
echo -e "${GREEN}  ✓ 已复制 requirements_proxy.txt${NC}"

cp "${SCRIPT_DIR}/docker/Dockerfile.proxy" "${PROJECT_ROOT}/docker/"
echo -e "${GREEN}  ✓ 已复制 docker/Dockerfile.proxy${NC}"

echo ""

# 步骤 6: 更新 docker-compose.yml
echo -e "${BLUE}步骤 6: 更新 docker-compose.yml...${NC}"

# 检查是否已经有 ragflow-proxy 服务
if grep -q "ragflow-proxy:" "${PROJECT_ROOT}/docker/docker-compose.yml"; then
    echo -e "${YELLOW}⚠️  docker-compose.yml 已包含 ragflow-proxy 服务${NC}"
else
    echo -e "${YELLOW}⚠️  需要手动添加 ragflow-proxy 服务到 docker-compose.yml${NC}"
    echo -e "${YELLOW}   参考: docker/local_codes/docker-compose-v-local-codes.yml${NC}"
fi

# 检查是否已经有文件挂载
if grep -q "langfuse_app.py:/ragflow/api/apps/langfuse_app.py" "${PROJECT_ROOT}/docker/docker-compose.yml"; then
    echo -e "${GREEN}✓ docker-compose.yml 已包含文件挂载${NC}"
else
    echo -e "${YELLOW}⚠️  需要手动添加文件挂载到 docker-compose.yml${NC}"
    echo -e "${YELLOW}   参考: docker/local_codes/docker-compose-v-local-codes.yml${NC}"
fi

echo ""

# 步骤 7: 更新 .env
echo -e "${BLUE}步骤 7: 检查 .env 配置...${NC}"

if grep -q "OTEL_SDK_DISABLED" "${PROJECT_ROOT}/docker/.env"; then
    echo -e "${GREEN}✓ .env 已包含 OTEL_SDK_DISABLED${NC}"
else
    echo -e "${YELLOW}⚠️  需要添加 OTEL_SDK_DISABLED=false 到 docker/.env${NC}"
fi

if grep -q "RAGFLOW_API_KEY" "${PROJECT_ROOT}/docker/.env"; then
    echo -e "${GREEN}✓ .env 已包含 RAGFLOW_API_KEY${NC}"
else
    echo -e "${YELLOW}⚠️  需要添加 RAGFLOW_API_KEY 到 docker/.env${NC}"
fi

if grep -q "PROXY_PORT" "${PROJECT_ROOT}/docker/.env"; then
    echo -e "${GREEN}✓ .env 已包含 PROXY_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  需要添加 PROXY_PORT=10101 到 docker/.env${NC}"
fi

echo ""

# 步骤 8: 生成待办事项清单
echo -e "${BLUE}步骤 8: 生成待办事项清单...${NC}"

TODO_FILE="${BACKUP_DIR}/TODO.md"
cat > "${TODO_FILE}" << 'EOF'
# RAGFlow v0.21.0 迁移待办事项

## ✅ 已完成
- [x] 创建备份
- [x] 运行差异对比
- [x] 复制低风险文件
- [x] 部署 OpenAI 代理服务文件

## ⚠️ 需要手动处理

### 高优先级
- [ ] 检查并添加 Agent ID 支持（如果需要）
  - 文件: `api/db/services/llm_service.py`
  - 参考: `docker/local_codes/MIGRATION_GUIDE_v0.21.md` 步骤 2.3

- [ ] 更新 docker-compose.yml
  - 添加 ragflow-proxy 服务
  - 添加文件挂载
  - 参考: `docker/local_codes/docker-compose-v-local-codes.yml`

- [ ] 更新 docker/.env
  - 添加 OTEL_SDK_DISABLED=false
  - 添加 RAGFLOW_API_KEY=your_api_key
  - 添加 PROXY_PORT=10101

### 中优先级
- [ ] 手动合并大文件
  - [ ] api/db/services/llm_service.py (375 行差异)
  - [ ] api/db/services/tenant_llm_service.py (75 行差异)
  - [ ] rag/llm/chat_model.py (275 行差异)
  - [ ] rag/utils/__init__.py (63 行差异)
  - [ ] rag/prompts/generator.py (375 行差异)
  - [ ] rag/flow/parser/parser.py (334 行差异)
  - [ ] rag/flow/tokenizer/tokenizer.py (43 行差异)
  
  使用命令:
  ```bash
  meld docker/local_codes/<file> <file>
  ```

- [ ] 迁移 Agent 组件
  - [ ] agent/canvas.py (25 行差异)
  - [ ] agent/component/llm.py (30 行差异)
  - [ ] agent/component/agent_with_tools.py (11 行差异)
  - [ ] agent/tools/retrieval.py (41 行差异)

- [ ] 处理 Chunker → Splitter 迁移
  - 源文件: `docker/local_codes/rag/flow/chunker/chunker.py`
  - 目标文件: `rag/flow/splitter/splitter.py`
  - 参考: `docker/local_codes/MIGRATION_GUIDE_v0.21.md` 步骤 5

### 低优先级
- [ ] 测试验证
  - [ ] 启动服务
  - [ ] 测试 Langfuse 集成
  - [ ] 测试 Agent 功能
  - [ ] 测试 OpenAI 代理
  - [ ] 检查日志错误

- [ ] 更新备份
  - [ ] 运行备份脚本
  - [ ] 更新文档

## 📚 参考文档
- 迁移分析: `docker/local_codes/MIGRATION_ANALYSIS_v0.21.md`
- 迁移指南: `docker/local_codes/MIGRATION_GUIDE_v0.21.md`
- 差异报告: `backup_YYYYMMDD_HHMMSS/diff_report.txt`

## 🔧 有用的命令

### 对比文件
```bash
meld docker/local_codes/<file> <file>
vimdiff docker/local_codes/<file> <file>
```

### 检查语法
```bash
python3 -m py_compile <file>
```

### 启动服务
```bash
cd docker
docker-compose up -d
docker-compose logs -f ragflow
```

### 测试 API
```bash
# Langfuse
curl -X GET http://localhost:9380/api/langfuse/api_key \
  -H "Authorization: Bearer YOUR_TOKEN"

# OpenAI 代理
curl http://localhost:10101/health
```
EOF

echo -e "${GREEN}✓ 待办事项清单已生成: ${TODO_FILE}${NC}"
echo ""

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}迁移总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ 已完成:${NC}"
echo -e "  - 创建备份: ${BACKUP_DIR}"
echo -e "  - 复制低风险文件"
echo -e "  - 部署 OpenAI 代理服务文件"
echo ""
echo -e "${YELLOW}⚠️  需要手动处理:${NC}"
echo -e "  - 检查 Agent ID 支持"
echo -e "  - 更新 docker-compose.yml"
echo -e "  - 更新 docker/.env"
echo -e "  - 手动合并大文件"
echo -e "  - 迁移 Agent 组件"
echo -e "  - 处理 Chunker → Splitter"
echo ""
echo -e "${BLUE}📋 下一步:${NC}"
echo -e "  1. 查看待办事项: cat ${TODO_FILE}"
echo -e "  2. 阅读迁移指南: cat docker/local_codes/MIGRATION_GUIDE_v0.21.md"
echo -e "  3. 手动处理剩余任务"
echo -e "  4. 测试验证"
echo ""
echo -e "${GREEN}迁移脚本执行完成！${NC}"

