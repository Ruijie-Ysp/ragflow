#!/bin/bash

# BrowserOS MCP Server 认证测试脚本
# 用于测试不同的认证方式

echo "=========================================="
echo "BrowserOS MCP Server 认证测试"
echo "=========================================="
echo ""

MCP_URL="http://127.0.0.1:9101/mcp"

echo "📋 测试 URL: $MCP_URL"
echo ""

# 检查 curl 是否可用
if ! command -v curl >/dev/null 2>&1; then
    echo "❌ curl 未安装，无法进行测试"
    exit 1
fi

echo "=========================================="
echo "测试 1: 无认证的 POST 请求"
echo "=========================================="
echo ""

curl -v -X POST "$MCP_URL" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
    2>&1 | grep -E "(HTTP|401|403|Unauthorized|Authorization)"

echo ""
echo ""

echo "=========================================="
echo "测试 2: 使用 Bearer Token"
echo "=========================================="
echo ""

echo "请输入 Bearer Token (如果有的话，直接回车跳过):"
read -r BEARER_TOKEN

if [ -n "$BEARER_TOKEN" ]; then
    curl -v -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $BEARER_TOKEN" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
        2>&1 | head -30
else
    echo "跳过 Bearer Token 测试"
fi

echo ""
echo ""

echo "=========================================="
echo "测试 3: 使用 API Key Header"
echo "=========================================="
echo ""

echo "请输入 API Key (如果有的话，直接回车跳过):"
read -r API_KEY

if [ -n "$API_KEY" ]; then
    curl -v -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
        2>&1 | head -30
else
    echo "跳过 API Key 测试"
fi

echo ""
echo ""

echo "=========================================="
echo "测试 4: 检查 BrowserOS 文档"
echo "=========================================="
echo ""

echo "BrowserOS MCP Server 可能需要以下认证方式之一："
echo ""
echo "1. Bearer Token:"
echo "   Authorization: Bearer <your-token>"
echo ""
echo "2. API Key:"
echo "   X-API-Key: <your-api-key>"
echo ""
echo "3. Basic Auth:"
echo "   Authorization: Basic <base64-encoded-credentials>"
echo ""
echo "4. 自定义 Header:"
echo "   可能需要特定的自定义 header"
echo ""

echo "=========================================="
echo "建议的解决方案"
echo "=========================================="
echo ""

echo "1. 检查 BrowserOS 扩展的设置页面"
echo "   → 查找 API Key 或 Token 配置"
echo ""
echo "2. 查看 BrowserOS 文档"
echo "   → 确认需要哪种认证方式"
echo ""
echo "3. 在 RAGFlow 中添加 MCP 服务器时："
echo "   → 点击 'Headers' 或 'Authorization' 选项"
echo "   → 添加正确的认证 header"
echo ""
echo "   示例 (Bearer Token):"
echo "   {"
echo "     \"Authorization\": \"Bearer your-token-here\""
echo "   }"
echo ""
echo "   示例 (API Key):"
echo "   {"
echo "     \"X-API-Key\": \"your-api-key-here\""
echo "   }"
echo ""

echo "=========================================="
echo "Docker 容器内测试"
echo "=========================================="
echo ""

if command -v docker >/dev/null 2>&1; then
    cd docker 2>/dev/null || true
    
    if docker compose ps ragflow-server | grep -q "Up"; then
        echo "从 Docker 容器内测试连接..."
        echo ""
        
        # 测试 host.docker.internal
        echo "测试 1: 使用 host.docker.internal:9101"
        docker compose exec -T ragflow-server sh -c "curl -v -X POST http://host.docker.internal:9101/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}'" 2>&1 | grep -E "(HTTP|401|403|Connection|refused)" || true
        echo ""
        
        # 获取宿主机 IP
        HOST_IP=$(docker compose exec -T ragflow-server sh -c "getent hosts host.docker.internal | awk '{ print \$1 }'" 2>/dev/null | tr -d '\r')
        
        if [ -n "$HOST_IP" ]; then
            echo "测试 2: 使用宿主机 IP: $HOST_IP:9101"
            docker compose exec -T ragflow-server sh -c "curl -v -X POST http://$HOST_IP:9101/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}'" 2>&1 | grep -E "(HTTP|401|403|Connection|refused)" || true
            echo ""
        fi
    fi
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""

