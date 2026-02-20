#!/bin/bash

# 恢复到 Docker 镜像中的最新版本
# 只恢复有差异的文件,保留当前代码的其他修改

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

RECOVERY_DIR="/tmp/ragflow_recovery_20251106_165326"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}恢复到最新版本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查恢复目录
if [ ! -d "$RECOVERY_DIR" ]; then
    echo -e "${RED}错误: 恢复目录不存在!${NC}"
    echo -e "${YELLOW}正在从 Docker 镜像提取代码...${NC}"
    ./recover_from_docker.sh
fi

echo -e "${YELLOW}[1/4] 分析差异...${NC}"
echo ""

# 检查 corpus_app.py
if ! diff -q "$RECOVERY_DIR/api/apps/corpus_app.py" api/apps/corpus_app.py > /dev/null 2>&1; then
    echo -e "${YELLOW}发现差异: api/apps/corpus_app.py${NC}"
    echo -e "  Docker 版本: $(wc -l < "$RECOVERY_DIR/api/apps/corpus_app.py" | tr -d ' ') 行"
    echo -e "  当前版本:   $(wc -l < api/apps/corpus_app.py | tr -d ' ') 行"
    NEED_RESTORE=1
else
    echo -e "${GREEN}✓ api/apps/corpus_app.py 已是最新${NC}"
    NEED_RESTORE=0
fi

echo ""

if [ $NEED_RESTORE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ 所有文件已是最新版本!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
fi

echo -e "${YELLOW}[2/4] 创建备份...${NC}"
BACKUP_DIR="backup_before_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp api/apps/corpus_app.py "$BACKUP_DIR/"
echo -e "${GREEN}✓ 备份到: $BACKUP_DIR${NC}"
echo ""

echo -e "${YELLOW}[3/4] 恢复文件...${NC}"
cp -v "$RECOVERY_DIR/api/apps/corpus_app.py" api/apps/corpus_app.py
echo -e "${GREEN}✓ 已恢复 api/apps/corpus_app.py${NC}"
echo ""

echo -e "${YELLOW}[4/4] 验证恢复...${NC}"
if diff -q "$RECOVERY_DIR/api/apps/corpus_app.py" api/apps/corpus_app.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 验证成功!${NC}"
else
    echo -e "${RED}✗ 验证失败!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 恢复完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}恢复的文件:${NC}"
echo -e "  ${GREEN}✓${NC} api/apps/corpus_app.py (393 行)"
echo ""
echo -e "${YELLOW}备份位置:${NC}"
echo -e "  ${BLUE}$BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}新增功能:${NC}"
echo -e "  ${GREEN}+${NC} 语料库统计 API (/statistics)"
echo -e "  ${GREEN}+${NC} 文档、分块、实体统计功能"
echo ""
echo -e "${GREEN}建议: 测试新功能是否正常工作${NC}"
echo ""
