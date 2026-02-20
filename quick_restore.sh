#!/bin/bash

# 快速恢复脚本
# 从 Docker 镜像提取的代码中恢复文件

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

RECOVERY_DIR="/tmp/ragflow_recovery_20251106_165326"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAGFlow 快速恢复工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查恢复目录
if [ ! -d "$RECOVERY_DIR" ]; then
    echo -e "${RED}错误: 恢复目录不存在!${NC}"
    echo -e "${YELLOW}请先运行: ./recover_from_docker.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}可用的恢复选项:${NC}"
echo ""
echo -e "  ${GREEN}1${NC}. 恢复 corpus_app.py (推荐)"
echo -e "  ${GREEN}2${NC}. 恢复所有 API 代码"
echo -e "  ${GREEN}3${NC}. 恢复所有 RAG 代码"
echo -e "  ${GREEN}4${NC}. 恢复所有 Agent 代码"
echo -e "  ${GREEN}5${NC}. 恢复所有代码 (完整恢复)"
echo -e "  ${GREEN}6${NC}. 备份提取的代码到安全位置"
echo -e "  ${GREEN}7${NC}. 查看差异"
echo -e "  ${GREEN}0${NC}. 退出"
echo ""

read -p "请选择 (0-7): " choice

case $choice in
    1)
        echo -e "${YELLOW}恢复 corpus_app.py...${NC}"
        cp -v "$RECOVERY_DIR/api/apps/corpus_app.py" api/apps/corpus_app.py
        echo -e "${GREEN}✓ 完成!${NC}"
        ;;
    2)
        echo -e "${YELLOW}恢复所有 API 代码...${NC}"
        read -p "确认要覆盖当前 api/ 目录吗? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            # 备份当前代码
            if [ -d "api" ]; then
                backup_dir="api.backup.$(date +%Y%m%d_%H%M%S)"
                echo -e "${BLUE}备份当前代码到: $backup_dir${NC}"
                cp -r api "$backup_dir"
            fi
            # 恢复
            cp -rv "$RECOVERY_DIR/api" ./
            echo -e "${GREEN}✓ 完成!${NC}"
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}恢复所有 RAG 代码...${NC}"
        read -p "确认要覆盖当前 rag/ 目录吗? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            # 备份当前代码
            if [ -d "rag" ]; then
                backup_dir="rag.backup.$(date +%Y%m%d_%H%M%S)"
                echo -e "${BLUE}备份当前代码到: $backup_dir${NC}"
                cp -r rag "$backup_dir"
            fi
            # 恢复
            cp -rv "$RECOVERY_DIR/rag" ./
            echo -e "${GREEN}✓ 完成!${NC}"
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        ;;
    4)
        echo -e "${YELLOW}恢复所有 Agent 代码...${NC}"
        read -p "确认要覆盖当前 agent/ 目录吗? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            # 备份当前代码
            if [ -d "agent" ]; then
                backup_dir="agent.backup.$(date +%Y%m%d_%H%M%S)"
                echo -e "${BLUE}备份当前代码到: $backup_dir${NC}"
                cp -r agent "$backup_dir"
            fi
            # 恢复
            cp -rv "$RECOVERY_DIR/agent" ./
            echo -e "${GREEN}✓ 完成!${NC}"
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        ;;
    5)
        echo -e "${RED}警告: 这将覆盖所有当前代码!${NC}"
        read -p "确认要完整恢复所有代码吗? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            # 备份当前代码
            backup_dir="ragflow_backup_$(date +%Y%m%d_%H%M%S)"
            echo -e "${BLUE}备份当前代码到: ~/$backup_dir${NC}"
            mkdir -p ~/"$backup_dir"
            for dir in api rag agent web conf deepdoc graphrag mcp plugin admin agentic_reasoning; do
                if [ -d "$dir" ]; then
                    cp -r "$dir" ~/"$backup_dir"/
                fi
            done
            
            # 恢复所有代码
            echo -e "${YELLOW}恢复所有代码...${NC}"
            cp -rv "$RECOVERY_DIR"/* ./
            echo -e "${GREEN}✓ 完成!${NC}"
            echo -e "${BLUE}备份位置: ~/$backup_dir${NC}"
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        ;;
    6)
        backup_dir=~/ragflow_from_docker_backup_$(date +%Y%m%d_%H%M%S)
        echo -e "${YELLOW}备份提取的代码到: $backup_dir${NC}"
        cp -r "$RECOVERY_DIR" "$backup_dir"
        echo -e "${GREEN}✓ 完成!${NC}"
        echo -e "${BLUE}备份位置: $backup_dir${NC}"
        ;;
    7)
        echo -e "${YELLOW}查看差异...${NC}"
        echo ""
        echo -e "${BLUE}corpus_app.py 差异:${NC}"
        diff -u api/apps/corpus_app.py "$RECOVERY_DIR/api/apps/corpus_app.py" | head -50 || true
        echo ""
        echo -e "${YELLOW}使用以下命令查看完整差异:${NC}"
        echo -e "  ${BLUE}diff -u api/apps/corpus_app.py $RECOVERY_DIR/api/apps/corpus_app.py${NC}"
        echo -e "  ${BLUE}meld api/ $RECOVERY_DIR/api/${NC}"
        ;;
    0)
        echo -e "${BLUE}退出${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}操作完成!${NC}"
echo -e "${BLUE}========================================${NC}"

