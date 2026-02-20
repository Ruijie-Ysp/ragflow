#!/bin/bash

# Docker镜像构建脚本 - 使用预编译的前端文件
# 此脚本会构建一个包含最新修复的Docker镜像

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  RAGFlow Docker 镜像构建"
echo "  使用预编译的前端文件"
echo "=========================================="
echo ""

# 检查 web/dist 目录
echo "1️⃣  检查预编译的前端文件..."
if [ ! -d "web/dist" ]; then
    echo "❌ 错误: web/dist 目录不存在!"
    echo "请先运行: cd web && npm run build"
    exit 1
fi

if [ ! -f "web/dist/umi.4fa99885.js" ]; then
    echo "⚠️  警告: 找不到预期的编译文件"
    echo "web/dist 目录内容:"
    ls -lh web/dist/*.js 2>&1 | head -5
fi

FILE_COUNT=$(find web/dist -type f | wc -l | tr -d ' ')
DIR_SIZE=$(du -sh web/dist | cut -f1)

echo "✅ web/dist 目录存在"
echo "   - 文件数量: $FILE_COUNT"
echo "   - 目录大小: $DIR_SIZE"
echo ""

# 检查 Docker
echo "2️⃣  检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装或不在 PATH 中"
    exit 1
fi

echo "✅ Docker 版本: $(docker --version)"
echo ""

# 设置镜像名称
IMAGE_NAME="infiniflow/ragflow:0.21-arm-new"
echo "3️⃣  准备构建镜像: $IMAGE_NAME"
echo ""

# 询问是否清理缓存
read -p "是否清理 Docker 构建缓存? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理 Docker 构建缓存..."
    docker builder prune -f
    echo ""
fi

# 开始构建
echo "4️⃣  开始构建 Docker 镜像..."
echo "   这可能需要几分钟时间..."
echo ""

BUILD_START=$(date +%s)

# 构建镜像
docker build \
    --build-arg LIGHTEN=1 \
    -f Dockerfile \
    -t "$IMAGE_NAME" \
    . \
    --progress=plain 2>&1 | tee docker_build.log

BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))

echo ""
echo "=========================================="
echo "  ✅ 构建完成!"
echo "=========================================="
echo ""
echo "📊 构建信息:"
echo "   - 镜像名称: $IMAGE_NAME"
echo "   - 构建时间: ${BUILD_TIME}秒"
echo "   - 构建日志: docker_build.log"
echo ""

# 检查镜像
echo "5️⃣  验证镜像..."
if docker images | grep -q "infiniflow/ragflow.*0.21-arm-new"; then
    echo "✅ 镜像创建成功"
    docker images | grep "infiniflow/ragflow.*0.21-arm-new"
else
    echo "❌ 错误: 镜像创建失败"
    exit 1
fi
echo ""

# 下一步提示
echo "=========================================="
echo "  📋 下一步操作"
echo "=========================================="
echo ""
echo "1. 更新 docker/.env 文件:"
echo "   RAGFLOW_IMAGE=$IMAGE_NAME"
echo ""
echo "2. 重启服务:"
echo "   cd docker"
echo "   docker compose down"
echo "   docker compose up -d"
echo ""
echo "3. 验证功能:"
echo "   - 访问 http://127.0.0.1"
echo "   - 检查数据库配置页面"
echo "   - 检查语料库页面"
echo ""
echo "=========================================="

