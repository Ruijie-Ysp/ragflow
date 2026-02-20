#!/bin/bash

echo "=========================================="
echo "设置 BrowserOS MCP Server 代理"
echo "=========================================="

# 检查是否已运行代理
PROXY_PORT=9102
if netstat -an | grep ":$PROXY_PORT " | grep -q LISTEN; then
    echo "⚠️  代理已在端口 $PROXY_PORT 运行"
    echo "停止现有代理..."
    pkill -f "socat.*$PROXY_PORT" 2>/dev/null || true
    sleep 2
fi

echo "🔧 启动 socat 代理..."
echo "   本地地址: 127.0.0.1:9101 -> 代理地址: 0.0.0.0:$PROXY_PORT"

# 使用 socat 创建代理
nohup socat TCP-LISTEN:$PROXY_PORT,fork,reuseaddr TCP:127.0.0.1:9101 > /tmp/socat_browseros.log 2>&1 &
SOCAT_PID=$!

echo "✅ 代理已启动 (PID: $SOCAT_PID)"
echo "📋 日志文件: /tmp/socat_browseros.log"

# 等待代理启动
sleep 3

# 验证代理是否工作
echo "🧪 测试代理连接..."
if curl -s -m 5 http://127.0.0.1:$PROXY_PORT/mcp > /dev/null; then
    echo "✅ 代理连接测试成功"
else
    echo "❌ 代理连接测试失败"
    kill $SOCAT_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=========================================="
echo "RAGFlow MCP 配置信息"
echo "=========================================="
echo "Name: BrowserOS"
echo "URL: http://host.docker.internal:$PROXY_PORT/mcp"
echo "Server Type: streamable-http"
echo "Authorization Token: (留空)"
echo ""

echo "=========================================="
echo "Docker 容器连接测试"
echo "=========================================="

# 测试从 Docker 容器连接
if docker exec ragflow-server curl -s -m 5 http://host.docker.internal:$PROXY_PORT/mcp > /dev/null 2>&1; then
    echo "✅ Docker 容器可以成功连接到 BrowserOS MCP Server"
else
    echo "❌ Docker 容器无法连接到 BrowserOS MCP Server"
    echo "🔍 检查代理状态..."
    ps aux | grep socat | grep $PROXY_PORT
fi

echo ""
echo "=========================================="
echo "管理命令"
echo "=========================================="
echo "查看代理状态: ps aux | grep socat | grep $PROXY_PORT"
echo "停止代理: pkill -f 'socat.*$PROXY_PORT'"
echo "查看日志: tail -f /tmp/socat_browseros.log"
echo ""
echo "代理将在后台持续运行，直到手动停止或系统重启。"
