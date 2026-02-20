#!/bin/bash

# RAGFlow 服务诊断脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAGFlow 服务诊断${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 查找 Docker 命令
DOCKER_CMD=""
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif [ -f "/usr/local/bin/docker" ]; then
    DOCKER_CMD="/usr/local/bin/docker"
elif [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    DOCKER_CMD="/Applications/Docker.app/Contents/Resources/bin/docker"
else
    echo -e "${RED}错误: 找不到 Docker 命令${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] 检查 Docker 版本...${NC}"
$DOCKER_CMD --version
echo ""

echo -e "${YELLOW}[2/6] 检查 RAGFlow 容器状态...${NC}"
echo ""
$DOCKER_CMD ps --filter "name=ragflow" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
echo ""

echo -e "${YELLOW}[3/6] 检查 Elasticsearch 状态...${NC}"
ES_CONTAINER=$($DOCKER_CMD ps --filter "name=es01" --format "{{.Names}}" | head -1)
if [ -n "$ES_CONTAINER" ]; then
    echo -e "${GREEN}✓ Elasticsearch 容器运行中: $ES_CONTAINER${NC}"
    # 测试连接
    $DOCKER_CMD exec "$ES_CONTAINER" curl -s http://localhost:9200/_cluster/health?pretty 2>/dev/null | grep -E "status|number_of_nodes" || echo "无法获取健康状态"
else
    echo -e "${RED}✗ Elasticsearch 容器未运行${NC}"
fi
echo ""

echo -e "${YELLOW}[4/6] 检查 Redis 状态...${NC}"
REDIS_CONTAINER=$($DOCKER_CMD ps --filter "name=redis" --format "{{.Names}}" | head -1)
if [ -n "$REDIS_CONTAINER" ]; then
    echo -e "${GREEN}✓ Redis 容器运行中: $REDIS_CONTAINER${NC}"
    # 测试连接
    REDIS_PING=$($DOCKER_CMD exec "$REDIS_CONTAINER" redis-cli -a infini_rag_flow ping 2>/dev/null || echo "FAIL")
    if [ "$REDIS_PING" = "PONG" ]; then
        echo -e "${GREEN}✓ Redis 连接正常${NC}"
    else
        echo -e "${RED}✗ Redis 连接失败${NC}"
    fi
else
    echo -e "${RED}✗ Redis 容器未运行${NC}"
fi
echo ""

echo -e "${YELLOW}[5/6] 检查 MySQL 状态...${NC}"
MYSQL_CONTAINER=$($DOCKER_CMD ps --filter "name=mysql" --format "{{.Names}}" | head -1)
if [ -n "$MYSQL_CONTAINER" ]; then
    echo -e "${GREEN}✓ MySQL 容器运行中: $MYSQL_CONTAINER${NC}"
else
    echo -e "${RED}✗ MySQL 容器未运行${NC}"
fi
echo ""

echo -e "${YELLOW}[6/6] 检查最近的警告和错误...${NC}"
echo ""
echo -e "${BLUE}--- RAGFlow Server 最近日志 ---${NC}"
SERVER_CONTAINER=$($DOCKER_CMD ps --filter "name=ragflow-server" --format "{{.Names}}" | head -1)
if [ -n "$SERVER_CONTAINER" ]; then
    $DOCKER_CMD logs --tail 20 "$SERVER_CONTAINER" 2>&1 | grep -E "WARNING|ERROR|INFO.*version" || echo "无警告或错误"
else
    echo -e "${RED}✗ RAGFlow Server 容器未运行${NC}"
fi
echo ""

echo -e "${BLUE}--- RAGFlow Executor 最近日志 ---${NC}"
EXECUTOR_CONTAINER=$($DOCKER_CMD ps --filter "name=ragflow-executor" --format "{{.Names}}" | head -1)
if [ -n "$EXECUTOR_CONTAINER" ]; then
    $DOCKER_CMD logs --tail 20 "$EXECUTOR_CONTAINER" 2>&1 | grep -E "WARNING|ERROR|INFO.*version|heartbeat" | tail -10 || echo "无警告或错误"
else
    echo -e "${RED}✗ RAGFlow Executor 容器未运行${NC}"
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}诊断总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 统计运行中的容器
RUNNING_COUNT=$($DOCKER_CMD ps --filter "name=ragflow" --format "{{.Names}}" | wc -l | tr -d ' ')
echo -e "运行中的 RAGFlow 容器: ${GREEN}$RUNNING_COUNT${NC}"

# 检查关键服务
CRITICAL_SERVICES=("ragflow-server" "ragflow-executor" "es01" "mysql" "redis")
CRITICAL_RUNNING=0
for service in "${CRITICAL_SERVICES[@]}"; do
    if $DOCKER_CMD ps --filter "name=$service" --format "{{.Names}}" | grep -q "$service"; then
        ((CRITICAL_RUNNING++))
    fi
done

echo -e "关键服务运行中: ${GREEN}$CRITICAL_RUNNING/${#CRITICAL_SERVICES[@]}${NC}"
echo ""

if [ $CRITICAL_RUNNING -eq ${#CRITICAL_SERVICES[@]} ]; then
    echo -e "${GREEN}✓ 所有关键服务正常运行!${NC}"
else
    echo -e "${YELLOW}⚠ 部分服务未运行,请检查${NC}"
fi

echo ""
echo -e "${YELLOW}访问地址:${NC}"
echo -e "  RAGFlow Web: ${BLUE}http://localhost:9380${NC}"
echo -e "  Admin Panel: ${BLUE}http://localhost:9381${NC}"
echo -e "  OpenAI Proxy: ${BLUE}http://localhost:10101${NC}"
echo -e "  MinIO Console: ${BLUE}http://localhost:9001${NC}"
echo ""

echo -e "${YELLOW}常用命令:${NC}"
echo -e "  查看日志: ${BLUE}$DOCKER_CMD logs -f ragflow-server${NC}"
echo -e "  重启服务: ${BLUE}cd docker && docker compose restart${NC}"
echo -e "  停止服务: ${BLUE}cd docker && docker compose down${NC}"
echo ""

