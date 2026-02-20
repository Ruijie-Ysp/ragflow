#!/bin/bash

# RAGFlow 优化部署脚本
set -e

RAGFLOW_DIR="/Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow"
cd "$RAGFLOW_DIR"

echo "========================================="
echo "RAGFlow 优化部署脚本"
echo "========================================="
echo ""

# 显示当前配置
echo "[1/4] 验证优化配置..."
echo ""
echo "✅ 并发配置:"
grep -E "(MAX_CONCURRENT|EMBEDDING_BATCH|DOC_BULK)" docker/.env | tail -6
echo ""
echo "✅ 内存配置:"
grep "MEM_LIMIT" docker/.env | tail -1
echo ""
echo "✅ Executor 配置:"
grep -A 2 "executor:" docker/docker-compose.yml | head -3
echo ""

# 停止当前服务
echo "[2/4] 停止当前服务..."
cd docker
docker-compose down
echo "✅ 服务已停止"
echo ""

# 启动优化后的服务
echo "[3/4] 启动优化后的服务..."
docker-compose up -d
echo "✅ 服务启动中..."
echo ""

# 等待服务就绪
echo "[4/4] 等待服务就绪..."
sleep 10

# 显示服务状态
echo ""
echo "========================================="
echo "服务状态"
echo "========================================="
docker-compose ps
echo ""

echo "========================================="
echo "资源使用情况"
echo "========================================="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

echo "🎉 部署完成!"
echo ""
echo "查看日志:"
echo "  - Executor: docker-compose logs -f executor"
echo "  - Server: docker-compose logs -f ragflow"
echo "  - 所有服务: docker-compose logs -f"
echo ""
echo "监控性能:"
echo "  - 实时资源: docker stats"
echo "  - 任务队列: docker logs ragflow-server 2>&1 | grep heartbeat"
echo ""

