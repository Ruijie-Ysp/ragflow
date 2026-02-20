#!/bin/bash

echo "🚀 启动 BrowserOS MCP 服务用于 VSCode Cline"
echo "================================================"

# 检查当前目录
CURRENT_DIR=$(pwd)
RAGFLOW_DIR="/Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow"

if [ "$CURRENT_DIR" != "$RAGFLOW_DIR" ]; then
    echo "📁 切换到 RAGFlow 目录..."
    cd "$RAGFLOW_DIR"
fi

# 检查 nginx 配置文件
if [ ! -f "nginx_proxy.conf" ]; then
    echo "❌ nginx_proxy.conf 文件不存在"
    exit 1
fi

# 停止现有的 nginx 进程
echo "🛑 停止现有的 nginx 代理..."
sudo nginx -s quit 2>/dev/null || true

# 等待进程完全停止
sleep 2

# 启动 nginx 代理
echo "🔧 启动 nginx 代理服务..."
sudo nginx -c $(pwd)/nginx_proxy.conf -p $(pwd)

if [ $? -eq 0 ]; then
    echo "✅ nginx 代理启动成功"
else
    echo "❌ nginx 代理启动失败"
    exit 1
fi

# 测试 MCP 服务连接
echo "🔍 测试 MCP 服务连接..."
sleep 2

RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"vscode-test","version":"1.0"}}}' \
    http://localhost:9102/mcp)

if [[ $RESPONSE == *"browseros_mcp"* ]]; then
    echo "✅ BrowserOS MCP 服务连接成功"
    echo ""
    echo "📋 服务信息:"
    echo "   - 代理地址: http://localhost:9102/mcp"
    echo "   - 协议版本: 2025-06-18"
    echo "   - 状态: 运行中"
    echo ""
    echo "🎯 下一步操作:"
    echo "   1. 重启 VSCode 或按 Cmd+Shift+P 并选择 'Developer: Reload Window'"
    echo "   2. 在 Cline 中即可使用 BrowserOS 工具"
    echo ""
    echo "📖 使用说明请查看: VSCode_CLINE_MCP_CONFIG.md"
else
    echo "❌ MCP 服务连接失败"
    echo "响应: $RESPONSE"
    exit 1
fi

echo ""
echo "🎉 BrowserOS MCP 服务已就绪！"
