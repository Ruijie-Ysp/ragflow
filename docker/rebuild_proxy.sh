#!/bin/bash

# RAGFlow OpenAI Proxy 重新构建脚本

set -e  # 遇到错误立即退出

echo "================================================================================"
echo "  RAGFlow OpenAI Proxy - 重新构建和启动"
echo "================================================================================"

# 切换到 docker 目录
cd "$(dirname "$0")"

echo ""
echo "📍 当前目录: $(pwd)"
echo ""

# 1. 停止现有容器
echo "🛑 停止现有的代理容器..."
docker-compose stop ragflow-proxy 2>/dev/null || true
docker-compose rm -f ragflow-proxy 2>/dev/null || true

echo ""
echo "✅ 容器已停止"
echo ""

# 2. 重新构建镜像
echo "🔨 重新构建代理镜像..."
echo "   这可能需要几分钟时间..."
echo ""

docker-compose build --no-cache ragflow-proxy

echo ""
echo "✅ 镜像构建完成"
echo ""

# 3. 启动容器
echo "🚀 启动代理容器..."
docker-compose up -d ragflow-proxy

echo ""
echo "✅ 容器已启动"
echo ""

# 4. 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 5

# 5. 检查容器状态
echo ""
echo "📊 容器状态:"
docker-compose ps ragflow-proxy

echo ""
echo "📋 容器日志 (最后 20 行):"
docker-compose logs --tail=20 ragflow-proxy

echo ""
echo "================================================================================"
echo "  重新构建完成！"
echo "================================================================================"
echo ""
echo "📝 下一步:"
echo "  1. 测试代理服务:"
echo "     curl http://localhost:10101/health"
echo ""
echo "  2. 查看实时日志:"
echo "     docker-compose logs -f ragflow-proxy"
echo ""
echo "  3. 运行测试脚本:"
echo "     cd local_codes"
echo "     python test_error_handling.py"
echo ""
echo "================================================================================"

