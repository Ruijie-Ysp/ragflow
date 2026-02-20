#!/bin/bash

# RAGFlow 修改代码恢复脚本
# 用途：将备份的代码文件恢复到 RAGFlow 项目中

set -e

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${BACKUP_DIR}/../.." && pwd)"

echo "🔄 RAGFlow 修改代码恢复工具"
echo "================================"
echo ""
echo "📁 备份目录: ${BACKUP_DIR}"
echo "📁 项目根目录: ${PROJECT_ROOT}"
echo ""

# 警告提示
echo "⚠️  警告: 此操作将覆盖项目中的文件！"
echo ""
read -p "是否继续？(yes/no) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ 操作已取消"
    exit 1
fi

# 定义需要恢复的文件列表
declare -a FILES=(
    "api/apps/langfuse_app.py"
    "api/db/services/llm_service.py"
    "api/db/services/tenant_llm_service.py"
    "rag/llm/chat_model.py"
    "rag/utils/__init__.py"
    "rag/prompts/generator.py"
    "rag/prompts/template.py"
    "rag/flow/parser/parser.py"
    "rag/flow/chunker/chunker.py"
    "rag/flow/tokenizer/tokenizer.py"
    "agent/canvas.py"
    "agent/component/llm.py"
    "agent/component/categorize.py"
    "agent/component/agent_with_tools.py"
    "agent/tools/retrieval.py"
)

# 恢复文件
echo "📋 开始恢复文件..."
RESTORE_COUNT=0
SKIP_COUNT=0

for file in "${FILES[@]}"; do
    SOURCE="${BACKUP_DIR}/${file}"
    DEST="${PROJECT_ROOT}/${file}"
    
    if [ -f "${SOURCE}" ]; then
        # 备份原文件（如果存在）
        if [ -f "${DEST}" ]; then
            BACKUP_FILE="${DEST}.backup-$(date +%Y%m%d-%H%M%S)"
            cp "${DEST}" "${BACKUP_FILE}"
            echo "  📦 备份原文件: ${file} -> ${file}.backup-*"
        fi
        
        echo "  ✅ 恢复: ${file}"
        cp "${SOURCE}" "${DEST}"
        ((RESTORE_COUNT++))
    else
        echo "  ⚠️  跳过（备份文件不存在）: ${file}"
        ((SKIP_COUNT++))
    fi
done

echo ""
echo "📊 恢复统计："
echo "  - 成功恢复: ${RESTORE_COUNT} 个文件"
echo "  - 跳过文件: ${SKIP_COUNT} 个文件"
echo ""
echo "✅ 恢复完成！"
echo ""
echo "📝 下一步："
echo "  1. 检查恢复的文件是否正确"
echo "  2. 重新构建 Docker 镜像"
echo "  3. 测试功能是否正常"
echo ""
