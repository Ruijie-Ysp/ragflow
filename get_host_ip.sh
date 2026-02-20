#!/bin/bash

# 获取宿主机 IP 地址的脚本

echo "=========================================="
echo "获取宿主机 IP 地址"
echo "=========================================="
echo ""

# 检测操作系统
OS="$(uname -s)"

case "${OS}" in
    Linux*)
        echo "检测到 Linux 系统"
        echo ""
        
        # 方法 1: 使用 hostname -I
        if command -v hostname >/dev/null 2>&1; then
            echo "方法 1: hostname -I"
            hostname -I | awk '{print $1}'
            echo ""
        fi
        
        # 方法 2: 使用 ip addr
        if command -v ip >/dev/null 2>&1; then
            echo "方法 2: ip addr"
            ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1
            echo ""
        fi
        
        # 方法 3: 使用 ifconfig
        if command -v ifconfig >/dev/null 2>&1; then
            echo "方法 3: ifconfig"
            ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
            echo ""
        fi
        ;;
        
    Darwin*)
        echo "检测到 macOS 系统"
        echo ""
        
        # 方法 1: WiFi (en0)
        echo "方法 1: WiFi (en0)"
        ipconfig getifaddr en0 2>/dev/null || echo "WiFi 未连接"
        echo ""
        
        # 方法 2: 以太网 (en1)
        echo "方法 2: 以太网 (en1)"
        ipconfig getifaddr en1 2>/dev/null || echo "以太网未连接"
        echo ""
        
        # 方法 3: 所有网络接口
        echo "方法 3: 所有网络接口"
        ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
        echo ""
        ;;
        
    *)
        echo "未知操作系统: ${OS}"
        echo ""
        
        # 尝试通用方法
        if command -v ifconfig >/dev/null 2>&1; then
            echo "使用 ifconfig:"
            ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
            echo ""
        fi
        ;;
esac

echo "=========================================="
echo "推荐的 RAGFlow MCP 配置"
echo "=========================================="
echo ""

# 获取第一个非 127.0.0.1 的 IP
if [ "${OS}" = "Darwin" ]; then
    # macOS: 优先使用 WiFi
    HOST_IP=$(ipconfig getifaddr en0 2>/dev/null)
    if [ -z "$HOST_IP" ]; then
        # 如果 WiFi 未连接，尝试以太网
        HOST_IP=$(ipconfig getifaddr en1 2>/dev/null)
    fi
    if [ -z "$HOST_IP" ]; then
        # 如果都没有，使用 ifconfig
        HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    fi
else
    # Linux
    if command -v hostname >/dev/null 2>&1; then
        HOST_IP=$(hostname -I | awk '{print $1}')
    elif command -v ip >/dev/null 2>&1; then
        HOST_IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1 | head -1)
    elif command -v ifconfig >/dev/null 2>&1; then
        HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    fi
fi

if [ -n "$HOST_IP" ]; then
    echo "检测到的宿主机 IP: $HOST_IP"
    echo ""
    echo "在 RAGFlow 中使用以下配置:"
    echo ""
    echo "  Name: BrowserOS"
    echo "  URL: http://$HOST_IP:9101/mcp"
    echo "  Server Type: streamable-http"
    echo "  Authorization Token: (留空)"
    echo ""
    
    # 测试连接
    echo "=========================================="
    echo "测试连接到 BrowserOS MCP Server"
    echo "=========================================="
    echo ""
    
    if command -v curl >/dev/null 2>&1; then
        echo "测试 URL: http://$HOST_IP:9101/mcp"
        echo ""
        
        curl -s -X POST "http://$HOST_IP:9101/mcp" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json, text/event-stream" \
            -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
            --max-time 5 \
            2>&1 | head -5
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 连接成功！"
        else
            echo ""
            echo "❌ 连接失败，请检查:"
            echo "   1. BrowserOS MCP Server 是否正在运行"
            echo "   2. 端口 9101 是否被监听"
            echo "   3. 防火墙设置"
        fi
    else
        echo "curl 未安装，无法测试连接"
    fi
else
    echo "❌ 无法检测到宿主机 IP"
    echo ""
    echo "请手动查找您的 IP 地址，然后在 RAGFlow 中使用:"
    echo "  URL: http://YOUR_IP:9101/mcp"
fi

echo ""
echo "=========================================="
echo "完成"
echo "=========================================="

