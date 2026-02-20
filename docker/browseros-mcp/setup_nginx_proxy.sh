#!/bin/bash

echo "=========================================="
echo "设置 BrowserOS MCP Server Nginx 代理"
echo "=========================================="

# 检查 nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo "📦 安装 nginx..."
    brew install nginx
fi

# 停止现有的 nginx 进程
echo "🛑 停止现有 nginx 进程..."
sudo nginx -s quit 2>/dev/null || true
sleep 2

# 停止现有的 socat 代理
echo "🛑 停止现有 socat 代理..."
pkill -f "socat.*9102" 2>/dev/null || true

PROXY_PORT=9103

echo "🔧 启动 nginx 代理..."
echo "   本地地址: 127.0.0.1:9101 -> 代理地址: 0.0.0.0:$PROXY_PORT"

# 启动 nginx
sudo nginx -c "$(pwd)/nginx_browseros_proxy.conf" -p "$(pwd)"

if [ $? -eq 0 ]; then
    echo "✅ Nginx 代理已启动"
    echo "📋 配置文件: $(pwd)/nginx_browseros_proxy.conf"
else
    echo "❌ Nginx 启动失败"
    exit 1
fi

# 等待 nginx 启动
sleep 3

# 验证代理是否工作
echo "🧪 测试代理连接..."
if curl -s -m 5 http://127.0.0.1:$PROXY_PORT/mcp > /dev/null; then
    echo "✅ 代理连接测试成功"
else
    echo "❌ 代理连接测试失败"
    sudo nginx -s quit 2>/dev/null
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
    echo "🔍 检查 nginx 状态..."
    ps aux | grep nginx | grep $PROXY_PORT
fi

echo ""
echo "=========================================="
echo "管理命令"
echo "=========================================="
echo "查看 nginx 状态: ps aux | grep nginx"
echo "停止代理: sudo nginx -s quit"
echo "重新加载配置: sudo nginx -s reload"
echo "测试配置: sudo nginx -t -c $(pwd)/nginx_browseros_proxy.conf"
echo ""
echo "代理将在后台持续运行，直到手动停止。"
