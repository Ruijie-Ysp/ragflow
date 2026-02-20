#!/bin/bash

# 对比 Docker 镜像中的代码和当前代码
# 创建时间: 2025-11-06

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

RECOVERY_DIR="/tmp/ragflow_recovery_20251106_165326"
CURRENT_DIR="$(pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker 代码对比分析${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查恢复目录是否存在
if [ ! -d "$RECOVERY_DIR" ]; then
    echo -e "${RED}错误: 恢复目录不存在: $RECOVERY_DIR${NC}"
    echo -e "${YELLOW}请先运行 ./recover_from_docker.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}对比目录:${NC}"
echo -e "  Docker: ${BLUE}$RECOVERY_DIR${NC}"
echo -e "  当前:   ${BLUE}$CURRENT_DIR${NC}"
echo ""

# 定义要对比的关键文件
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
    "uv.lock"
)

declare -A FILE_DESC=(
    ["api/apps/langfuse_app.py"]="Langfuse集成"
    ["api/apps/mcp_server_app.py"]="MCP服务器"
    ["api/apps/corpus_app.py"]="语料库应用"
    ["api/db/services/llm_service.py"]="LLM服务"
    ["api/db/services/tenant_llm_service.py"]="租户LLM服务"
    ["rag/llm/chat_model.py"]="聊天模型"
    ["rag/svr/task_executor.py"]="任务执行器"
    ["agent/canvas.py"]="Agent画布"
    ["agent/component/llm.py"]="LLM组件"
    ["pyproject.toml"]="项目配置"
    ["uv.lock"]="依赖锁定"
)

echo -e "${YELLOW}关键文件对比:${NC}"
echo ""

SAME_COUNT=0
DIFF_COUNT=0
MISSING_COUNT=0

for file in "${KEY_FILES[@]}"; do
    desc="${FILE_DESC[$file]}"
    docker_file="$RECOVERY_DIR/$file"
    current_file="$CURRENT_DIR/$file"

    printf "%-45s %-20s " "$file" "($desc)"

    if [ ! -f "$docker_file" ]; then
        echo -e "${RED}✗ Docker中不存在${NC}"
        ((MISSING_COUNT++))
    elif [ ! -f "$current_file" ]; then
        echo -e "${YELLOW}⚠ 当前不存在${NC}"
        ((MISSING_COUNT++))
    elif diff -q "$docker_file" "$current_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 相同${NC}"
        ((SAME_COUNT++))
    else
        echo -e "${RED}✗ 有差异${NC}"
        ((DIFF_COUNT++))
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}统计:${NC}"
echo -e "  ${GREEN}相同: $SAME_COUNT${NC}"
echo -e "  ${RED}有差异: $DIFF_COUNT${NC}"
echo -e "  ${YELLOW}缺失: $MISSING_COUNT${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 对比目录结构
echo -e "${YELLOW}目录结构对比:${NC}"
echo ""

for dir in api rag agent web conf; do
    docker_dir="$RECOVERY_DIR/$dir"
    current_dir="$CURRENT_DIR/$dir"
    
    if [ -d "$docker_dir" ] && [ -d "$current_dir" ]; then
        docker_count=$(find "$docker_dir" -type f | wc -l | tr -d ' ')
        current_count=$(find "$current_dir" -type f | wc -l | tr -d ' ')
        
        printf "%-10s Docker: %4d 文件  当前: %4d 文件  " "$dir" "$docker_count" "$current_count"
        
        if [ "$docker_count" -eq "$current_count" ]; then
            echo -e "${GREEN}✓ 相同${NC}"
        elif [ "$docker_count" -gt "$current_count" ]; then
            diff=$((docker_count - current_count))
            echo -e "${YELLOW}⚠ Docker 多 $diff 个文件${NC}"
        else
            diff=$((current_count - docker_count))
            echo -e "${YELLOW}⚠ 当前多 $diff 个文件${NC}"
        fi
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}详细差异分析:${NC}"
echo ""

# 显示有差异的文件的详细信息
for file in "${KEY_FILES[@]}"; do
    docker_file="$RECOVERY_DIR/$file"
    current_file="$CURRENT_DIR/$file"

    if [ -f "$docker_file" ] && [ -f "$current_file" ]; then
        if ! diff -q "$docker_file" "$current_file" > /dev/null 2>&1; then
            echo -e "${RED}文件有差异: $file${NC}"
            echo -e "${YELLOW}Docker 版本:${NC}"
            ls -lh "$docker_file" | awk '{print "  大小: " $5 "  修改时间: " $6 " " $7 " " $8}'
            echo -e "${YELLOW}当前版本:${NC}"
            ls -lh "$current_file" | awk '{print "  大小: " $5 "  修改时间: " $6 " " $7 " " $8}'

            # 显示行数差异
            docker_lines=$(wc -l < "$docker_file" | tr -d ' ')
            current_lines=$(wc -l < "$current_file" | tr -d ' ')
            echo -e "${YELLOW}行数:${NC} Docker: $docker_lines  当前: $current_lines"
            echo ""
        fi
    fi
done

echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}建议操作:${NC}"
echo ""

if [ $SAME_COUNT -eq ${#KEY_FILES[@]} ]; then
    echo -e "${GREEN}✓ 所有关键文件都相同,无需恢复!${NC}"
elif [ $DIFF_COUNT -gt 0 ]; then
    echo -e "${YELLOW}发现 $DIFF_COUNT 个文件有差异,建议:${NC}"
    echo ""
    echo -e "1. 查看具体差异:"
    for file in "${KEY_FILES[@]}"; do
        docker_file="$RECOVERY_DIR/$file"
        current_file="$CURRENT_DIR/$file"
        if [ -f "$docker_file" ] && [ -f "$current_file" ]; then
            if ! diff -q "$docker_file" "$current_file" > /dev/null 2>&1; then
                echo -e "   ${BLUE}diff $docker_file $current_file${NC}"
            fi
        fi
    done
    echo ""
    echo -e "2. 使用可视化工具对比:"
    echo -e "   ${BLUE}meld $RECOVERY_DIR $CURRENT_DIR${NC}"
    echo ""
    echo -e "3. 恢复特定文件:"
    for file in "${KEY_FILES[@]}"; do
        docker_file="$RECOVERY_DIR/$file"
        current_file="$CURRENT_DIR/$file"
        if [ -f "$docker_file" ] && [ -f "$current_file" ]; then
            if ! diff -q "$docker_file" "$current_file" > /dev/null 2>&1; then
                echo -e "   ${BLUE}cp $docker_file $current_file${NC}"
            fi
        fi
    done
fi

if [ $MISSING_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}发现 $MISSING_COUNT 个文件缺失,建议检查!${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

