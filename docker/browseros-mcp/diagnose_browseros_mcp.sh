#!/bin/bash

# BrowserOS MCP Server 诊断脚本
# 用于检查 BrowserOS MCP Server 是否正常运行

echo "=========================================="
echo "BrowserOS MCP Server 诊断"
echo "=========================================="
echo ""

echo "📋 Step 1: 检查端口 9101 是否被监听..."
echo ""

# 检查端口 9101 是否被监听
if lsof -i :9101 >/dev/null 2>&1; then
    echo "✅ 端口 9101 正在被监听"
    echo ""
    echo "进程信息："
    lsof -i :9101
    echo ""
elif netstat -an 2>/dev/null | grep -q ":9101.*LISTEN"; then
    echo "✅ 端口 9101 正在被监听"
    echo ""
    echo "连接信息："
    netstat -an | grep ":9101"
    echo ""
else
    echo "❌ 端口 9101 没有被监听！"
    echo ""
    echo "这意味着 BrowserOS MCP Server 没有运行。"
    echo ""
    echo "请检查："
    echo "  1. BrowserOS 扩展是否已安装"
    echo "  2. BrowserOS MCP Server 是否已启动"
    echo "  3. 配置的端口是否确实是 9101"
    echo ""
    exit 1
fi

echo "📋 Step 2: 测试 HTTP 连接..."
echo ""

# 测试 HTTP 连接
if command -v curl >/dev/null 2>&1; then
    echo "使用 curl 测试连接到 http://127.0.0.1:9101/mcp ..."
    echo ""
    
    # 尝试 GET 请求
    echo "--- GET 请求 ---"
    curl -v http://127.0.0.1:9101/mcp 2>&1 | head -20
    echo ""
    
    # 尝试 POST 请求（MCP 协议）
    echo "--- POST 请求（测试 MCP 协议）---"
    curl -v -X POST http://127.0.0.1:9101/mcp \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' 2>&1 | head -20
    echo ""
else
    echo "⚠️  curl 未安装，跳过 HTTP 测试"
    echo ""
fi

echo "📋 Step 3: 检查 Docker 网络..."
echo ""

# 检查 Docker 容器是否能访问宿主机的 9101 端口
if command -v docker >/dev/null 2>&1; then
    echo "从 Docker 容器内测试连接..."
    echo ""
    
    cd docker 2>/dev/null || cd .
    
    if docker compose ps ragflow-server | grep -q "Up"; then
        echo "测试从 ragflow-server 容器访问 host.docker.internal:9101 ..."
        docker compose exec -T ragflow-server sh -c "curl -v http://host.docker.internal:9101/mcp" 2>&1 | head -20 || true
        echo ""
        
        echo "测试从 ragflow-server 容器访问 127.0.0.1:9101 ..."
        docker compose exec -T ragflow-server sh -c "curl -v http://127.0.0.1:9101/mcp" 2>&1 | head -20 || true
        echo ""
    else
        echo "⚠️  ragflow-server 容器未运行"
        echo ""
    fi
else
    echo "⚠️  Docker 未安装或不可用"
    echo ""
fi

echo "📋 Step 4: 检查防火墙..."
echo ""

# 检查防火墙（macOS）
if command -v pfctl >/dev/null 2>&1; then
    echo "检查 macOS 防火墙状态..."
    sudo pfctl -s info 2>/dev/null | grep -i "status" || echo "需要 sudo 权限"
    echo ""
fi

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "📝 建议："
echo ""
echo "1. 如果端口 9101 没有被监听："
echo "   → 启动 BrowserOS MCP Server"
echo ""
echo "2. 如果端口被监听但连接失败："
echo "   → 检查 BrowserOS 配置"
echo "   → 确认 server type 是否正确（sse 或 streamable-http）"
echo ""
echo "3. 如果从 Docker 容器无法访问："
echo "   → 使用 host.docker.internal 而不是 127.0.0.1"
echo "   → 或者使用宿主机的实际 IP 地址"
echo ""
echo "4. 测试正确的 URL："
echo "   → SSE: http://host.docker.internal:9101/sse"
echo "   → Streamable HTTP: http://host.docker.internal:9101/mcp"
echo ""

