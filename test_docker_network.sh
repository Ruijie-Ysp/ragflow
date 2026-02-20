#!/bin/bash

echo "=========================================="
echo "测试 Docker 容器网络连接"
echo "=========================================="
echo ""

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 命令不可用"
    exit 1
fi

echo "1️⃣ 检查 ragflow-server 容器是否运行..."
if docker ps | grep -q ragflow-server; then
    echo "✅ ragflow-server 容器正在运行"
else
    echo "❌ ragflow-server 容器未运行"
    exit 1
fi

echo ""
echo "2️⃣ 检查容器内的 /etc/hosts..."
docker exec ragflow-server cat /etc/hosts | grep -E "host.docker.internal|127.0.0.1"

echo ""
echo "3️⃣ 测试从容器内访问 host.docker.internal:9101..."
docker exec ragflow-server curl -v -X POST http://host.docker.internal:9101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  --max-time 5 2>&1 | head -30

echo ""
echo "4️⃣ 测试从容器内访问 127.0.0.1:9101..."
docker exec ragflow-server curl -v -X POST http://127.0.0.1:9101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  --max-time 5 2>&1 | head -30

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="

