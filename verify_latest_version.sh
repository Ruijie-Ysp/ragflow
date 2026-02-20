#!/bin/bash

# 验证当前代码是否为最新版本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

RECOVERY_DIR="/tmp/ragflow_recovery_20251106_165326"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}验证代码版本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -d "$RECOVERY_DIR" ]; then
    echo -e "${RED}错误: 恢复目录不存在!${NC}"
    exit 1
fi

echo -e "${YELLOW}对比关键文件...${NC}"
echo ""

# 定义关键文件
declare -a KEY_FILES=(
    "api/apps/langfuse_app.py"
    "api/apps/mcp_server_app.py"
    "api/apps/corpus_app.py"
    "api/db/services/llm_service.py"
    "api/db/services/tenant_llm_service.py"
    "rag/llm/chat_model.py"
    "rag/svr/task_executor.py"
    "agent/canvas.py"
    "agent/component/llm.py"
    "pyproject.toml"
)

SAME_COUNT=0
DIFF_COUNT=0
MISSING_COUNT=0

for file in "${KEY_FILES[@]}"; do
    docker_file="$RECOVERY_DIR/$file"
    current_file="$file"
    
    printf "%-45s " "$file"
    
    if [ ! -f "$docker_file" ]; then
        echo -e "${RED}✗ Docker中不存在${NC}"
        ((MISSING_COUNT++))
    elif [ ! -f "$current_file" ]; then
        echo -e "${YELLOW}⚠ 当前不存在${NC}"
        ((MISSING_COUNT++))
    elif diff -q "$docker_file" "$current_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 最新版本${NC}"
        ((SAME_COUNT++))
    else
        echo -e "${RED}✗ 有差异${NC}"
        ((DIFF_COUNT++))
        
        # 显示详细信息
        docker_lines=$(wc -l < "$docker_file" | tr -d ' ')
        current_lines=$(wc -l < "$current_file" | tr -d ' ')
        echo -e "    Docker: $docker_lines 行  当前: $current_lines 行"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}统计结果:${NC}"
echo -e "  ${GREEN}最新版本: $SAME_COUNT${NC}"
echo -e "  ${RED}有差异:   $DIFF_COUNT${NC}"
echo -e "  ${YELLOW}缺失:     $MISSING_COUNT${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $SAME_COUNT -eq ${#KEY_FILES[@]} ]; then
    echo -e "${GREEN}✓✓✓ 恭喜! 所有关键文件都是最新版本! ✓✓✓${NC}"
    echo ""
    echo -e "${BLUE}当前代码版本信息:${NC}"
    if [ -f "VERSION" ]; then
        echo -e "  版本: ${GREEN}$(cat VERSION)${NC}"
    fi
    echo -e "  来源: ${GREEN}Docker 镜像 infiniflow/ragflow:0.21-arm-1106-1${NC}"
    echo -e "  构建时间: ${GREEN}2025-11-06 13:21:02${NC}"
    echo ""
    echo -e "${YELLOW}包含的关键功能:${NC}"
    echo -e "  ${GREEN}✓${NC} Langfuse 集成"
    echo -e "  ${GREEN}✓${NC} MCP 服务器"
    echo -e "  ${GREEN}✓${NC} 语料库统计 API"
    echo -e "  ${GREEN}✓${NC} 任务执行器优化"
    echo -e "  ${GREEN}✓${NC} Agent 核心功能"
    echo ""
elif [ $DIFF_COUNT -gt 0 ]; then
    echo -e "${YELLOW}发现 $DIFF_COUNT 个文件有差异${NC}"
    echo ""
    echo -e "${YELLOW}建议操作:${NC}"
    echo -e "  1. 查看差异: ${BLUE}./compare_docker_code.sh${NC}"
    echo -e "  2. 恢复文件: ${BLUE}./quick_restore.sh${NC}"
    echo ""
fi

# 检查备份
echo -e "${YELLOW}检查备份...${NC}"
if [ -d ~/ragflow_from_docker_backup ]; then
    echo -e "  ${GREEN}✓${NC} 已有备份: ~/ragflow_from_docker_backup"
else
    echo -e "  ${YELLOW}⚠${NC} 建议创建备份:"
    echo -e "    ${BLUE}cp -r $RECOVERY_DIR ~/ragflow_from_docker_backup${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

