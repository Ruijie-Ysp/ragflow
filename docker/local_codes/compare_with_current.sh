#!/bin/bash

# RAGFlow 代码差异对比脚本
# 用途：对比备份文件和当前项目文件的差异

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${BACKUP_DIR}/../.." && pwd)"

echo "🔍 RAGFlow 代码差异对比工具"
echo "================================"
echo ""

# 定义需要对比的文件列表
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

DIFF_COUNT=0
SAME_COUNT=0
MISSING_COUNT=0

for file in "${FILES[@]}"; do
    BACKUP_FILE="${BACKUP_DIR}/${file}"
    CURRENT_FILE="${PROJECT_ROOT}/${file}"
    
    if [ ! -f "${BACKUP_FILE}" ]; then
        echo "⚠️  备份文件不存在: ${file}"
        ((MISSING_COUNT++))
        continue
    fi
    
    if [ ! -f "${CURRENT_FILE}" ]; then
        echo "⚠️  当前文件不存在: ${file}"
        ((MISSING_COUNT++))
        continue
    fi
    
    if diff -q "${BACKUP_FILE}" "${CURRENT_FILE}" > /dev/null 2>&1; then
        echo "✅ 相同: ${file}"
        ((SAME_COUNT++))
    else
        echo "🔄 有差异: ${file}"
        ((DIFF_COUNT++))
        
        # 显示差异摘要
        echo "   差异行数: $(diff "${BACKUP_FILE}" "${CURRENT_FILE}" | grep -c '^[<>]')"
        
        # 询问是否查看详细差异
        if [ "${1}" == "--verbose" ] || [ "${1}" == "-v" ]; then
            echo "   ----------------------------------------"
            diff -u "${BACKUP_FILE}" "${CURRENT_FILE}" || true
            echo "   ----------------------------------------"
        fi
    fi
done

echo ""
echo "📊 对比统计："
echo "  - 相同文件: ${SAME_COUNT} 个"
echo "  - 有差异文件: ${DIFF_COUNT} 个"
echo "  - 缺失文件: ${MISSING_COUNT} 个"
echo ""

if [ ${DIFF_COUNT} -gt 0 ]; then
    echo "💡 提示: 使用 --verbose 或 -v 参数查看详细差异"
    echo "   示例: ./compare_with_current.sh --verbose"
fi
