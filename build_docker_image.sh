#!/bin/bash

# RAGFlow Docker镜像构建脚本
# 确保前端编译成功

set -e  # 遇到错误立即退出

echo "=========================================="
echo "RAGFlow Docker 镜像构建脚本"
echo "=========================================="
echo ""

# 配置
IMAGE_NAME="infiniflow/ragflow"
IMAGE_TAG="0.21-arm-new"
DOCKERFILE="Dockerfile"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否运行
echo -e "${YELLOW}[1/5] 检查 Docker 环境...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误: Docker 未运行,请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 运行正常${NC}"
echo ""

# 清理旧的构建缓存(可选)
read -p "是否清理 Docker 构建缓存? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[2/5] 清理 Docker 构建缓存...${NC}"
    docker builder prune -f
    echo -e "${GREEN}✓ 缓存清理完成${NC}"
else
    echo -e "${YELLOW}[2/5] 跳过缓存清理${NC}"
fi
echo ""

# 检查必要文件
echo -e "${YELLOW}[3/5] 检查必要文件...${NC}"
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}错误: 找不到 $DOCKERFILE${NC}"
    exit 1
fi
if [ ! -d "web" ]; then
    echo -e "${RED}错误: 找不到 web 目录${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 文件检查通过${NC}"
echo ""

# 开始构建
echo -e "${YELLOW}[4/5] 开始构建 Docker 镜像...${NC}"
echo "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "构建参数: LIGHTEN=1"
echo ""

# 构建命令
docker build \
    --build-arg LIGHTEN=1 \
    --build-arg NEED_MIRROR=0 \
    -f "$DOCKERFILE" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    --progress=plain \
    . 2>&1 | tee docker_build.log

# 检查构建结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "✓ 镜像构建成功!"
    echo -e "==========================================${NC}"
    echo ""
    echo "镜像信息:"
    docker images "${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo -e "${YELLOW}[5/5] 下一步操作:${NC}"
    echo "1. 更新 docker/.env 文件中的镜像名称:"
    echo "   RAGFLOW_IMAGE=${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "2. 重启服务:"
    echo "   cd docker && docker compose down && docker compose up -d"
    echo ""
    echo "构建日志已保存到: docker_build.log"
else
    echo ""
    echo -e "${RED}=========================================="
    echo -e "✗ 镜像构建失败!"
    echo -e "==========================================${NC}"
    echo ""
    echo "请检查构建日志: docker_build.log"
    echo ""
    echo "常见问题排查:"
    echo "1. 检查网络连接是否正常"
    echo "2. 检查 Docker 磁盘空间是否充足"
    echo "3. 查看日志中的具体错误信息"
    exit 1
fi

