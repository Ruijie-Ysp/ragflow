#!/bin/bash

# RAGFlow 代码恢复脚本
# 从 Docker 镜像 docker.io/infiniflow/ragflow:0.21-arm-1106-1 中恢复代码
# 创建时间: 2025-11-06

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DOCKER_IMAGE="infiniflow/ragflow:0.21-arm-1106-1"
TEMP_CONTAINER="ragflow_recovery_temp"
RECOVERY_DIR="/tmp/ragflow_recovery_$(date +%Y%m%d_%H%M%S)"
CURRENT_DIR="$(pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAGFlow 代码恢复工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Docker 是否可用
echo -e "${YELLOW}[1/7] 检查 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    if [ -f "/usr/local/bin/docker" ]; then
        DOCKER_CMD="/usr/local/bin/docker"
        echo -e "${GREEN}✓ 找到 Docker: $DOCKER_CMD${NC}"
    else
        echo -e "${RED}✗ 错误: 找不到 Docker 命令${NC}"
        exit 1
    fi
else
    DOCKER_CMD="docker"
    echo -e "${GREEN}✓ Docker 已安装${NC}"
fi

# 检查镜像是否存在
echo -e "${YELLOW}[2/7] 检查 Docker 镜像...${NC}"
if ! $DOCKER_CMD images | grep -q "0.21-arm-1106-1"; then
    echo -e "${RED}✗ 错误: 找不到镜像 $DOCKER_IMAGE${NC}"
    echo -e "${YELLOW}提示: 请确认镜像名称是否正确${NC}"
    $DOCKER_CMD images | grep ragflow
    exit 1
fi
echo -e "${GREEN}✓ 镜像存在: $DOCKER_IMAGE${NC}"

# 获取镜像创建时间
IMAGE_DATE=$($DOCKER_CMD inspect $DOCKER_IMAGE --format='{{.Created}}' | cut -d'T' -f1)
echo -e "${BLUE}  镜像创建时间: $IMAGE_DATE${NC}"

# 创建恢复目录
echo -e "${YELLOW}[3/7] 创建恢复目录...${NC}"
mkdir -p "$RECOVERY_DIR"
echo -e "${GREEN}✓ 恢复目录: $RECOVERY_DIR${NC}"

# 创建临时容器
echo -e "${YELLOW}[4/7] 创建临时容器...${NC}"
# 先清理可能存在的旧容器
$DOCKER_CMD rm -f $TEMP_CONTAINER 2>/dev/null || true
CONTAINER_ID=$($DOCKER_CMD create --name $TEMP_CONTAINER $DOCKER_IMAGE)
echo -e "${GREEN}✓ 容器 ID: ${CONTAINER_ID:0:12}${NC}"

# 从容器中提取代码
echo -e "${YELLOW}[5/7] 从 Docker 镜像提取代码...${NC}"

# 定义要提取的目录和文件
DIRS_TO_EXTRACT=(
    "api"
    "rag"
    "agent"
    "web"
    "conf"
    "deepdoc"
    "graphrag"
    "mcp"
    "plugin"
    "admin"
    "agentic_reasoning"
)

FILES_TO_EXTRACT=(
    "pyproject.toml"
    "uv.lock"
    "VERSION"
)

# 提取目录
for dir in "${DIRS_TO_EXTRACT[@]}"; do
    echo -e "  提取: ${BLUE}$dir${NC}"
    if $DOCKER_CMD cp $TEMP_CONTAINER:/ragflow/$dir "$RECOVERY_DIR/" 2>/dev/null; then
        SIZE=$(du -sh "$RECOVERY_DIR/$dir" | cut -f1)
        echo -e "    ${GREEN}✓ 成功 ($SIZE)${NC}"
    else
        echo -e "    ${YELLOW}⚠ 跳过 (不存在)${NC}"
    fi
done

# 提取文件
for file in "${FILES_TO_EXTRACT[@]}"; do
    echo -e "  提取: ${BLUE}$file${NC}"
    if $DOCKER_CMD cp $TEMP_CONTAINER:/ragflow/$file "$RECOVERY_DIR/" 2>/dev/null; then
        echo -e "    ${GREEN}✓ 成功${NC}"
    else
        echo -e "    ${YELLOW}⚠ 跳过 (不存在)${NC}"
    fi
done

# 清理临时容器
echo -e "${YELLOW}[6/7] 清理临时容器...${NC}"
$DOCKER_CMD rm $TEMP_CONTAINER > /dev/null
echo -e "${GREEN}✓ 已清理${NC}"

# 生成恢复报告
echo -e "${YELLOW}[7/7] 生成恢复报告...${NC}"

REPORT_FILE="$RECOVERY_DIR/RECOVERY_REPORT.md"
cat > "$REPORT_FILE" << EOF
# RAGFlow 代码恢复报告

## 恢复信息
- **恢复时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **Docker 镜像**: $DOCKER_IMAGE
- **镜像创建时间**: $IMAGE_DATE
- **恢复目录**: $RECOVERY_DIR

## 提取的文件

### 目录
EOF

for dir in "${DIRS_TO_EXTRACT[@]}"; do
    if [ -d "$RECOVERY_DIR/$dir" ]; then
        SIZE=$(du -sh "$RECOVERY_DIR/$dir" | cut -f1)
        FILE_COUNT=$(find "$RECOVERY_DIR/$dir" -type f | wc -l | tr -d ' ')
        echo "- ✓ \`$dir\` - $SIZE ($FILE_COUNT 个文件)" >> "$REPORT_FILE"
    fi
done

echo "" >> "$REPORT_FILE"
echo "### 文件" >> "$REPORT_FILE"

for file in "${FILES_TO_EXTRACT[@]}"; do
    if [ -f "$RECOVERY_DIR/$file" ]; then
        SIZE=$(ls -lh "$RECOVERY_DIR/$file" | awk '{print $5}')
        echo "- ✓ \`$file\` - $SIZE" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << 'EOF'

## 下一步操作

### 选项 1: 完整恢复 (推荐用于完全丢失代码的情况)

```bash
# 备份当前代码 (如果有)
cp -r api api.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp -r rag rag.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
cp -r agent agent.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# 恢复所有代码
RECOVERY_DIR="<恢复目录路径>"
cp -r $RECOVERY_DIR/api ./
cp -r $RECOVERY_DIR/rag ./
cp -r $RECOVERY_DIR/agent ./
cp -r $RECOVERY_DIR/web ./
cp -r $RECOVERY_DIR/conf ./
cp -r $RECOVERY_DIR/deepdoc ./
cp -r $RECOVERY_DIR/graphrag ./
cp -r $RECOVERY_DIR/mcp ./
cp -r $RECOVERY_DIR/plugin ./
cp $RECOVERY_DIR/pyproject.toml ./
cp $RECOVERY_DIR/uv.lock ./
```

### 选项 2: 选择性恢复 (推荐用于部分代码丢失的情况)

```bash
# 只恢复特定目录
RECOVERY_DIR="<恢复目录路径>"

# 例如: 只恢复 api 目录
cp -r $RECOVERY_DIR/api ./

# 例如: 只恢复 rag 目录
cp -r $RECOVERY_DIR/rag ./
```

### 选项 3: 对比差异后恢复

```bash
# 对比差异
RECOVERY_DIR="<恢复目录路径>"

# 对比 api 目录
diff -r $RECOVERY_DIR/api ./api

# 对比 rag 目录
diff -r $RECOVERY_DIR/rag ./rag

# 使用 meld 或其他工具进行可视化对比
meld $RECOVERY_DIR/api ./api
```

## 验证恢复

恢复后,请执行以下检查:

1. **检查文件完整性**
   ```bash
   ls -la api/
   ls -la rag/
   ls -la agent/
   ```

2. **检查关键文件**
   ```bash
   # 检查是否存在关键的 Python 文件
   find api -name "*.py" | head -10
   find rag -name "*.py" | head -10
   find agent -name "*.py" | head -10
   ```

3. **测试构建**
   ```bash
   # 尝试构建 Docker 镜像
   docker build --build-arg LIGHTEN=1 -f Dockerfile -t ragflow:test .
   ```

## 注意事项

1. **时间戳**: 从 Docker 镜像提取的文件时间戳可能与原始文件不同
2. **权限**: 提取的文件权限可能需要调整
3. **依赖**: 确保 pyproject.toml 和 uv.lock 也已恢复
4. **配置**: conf 目录中的配置文件可能需要根据实际环境调整

## 故障排查

如果恢复后遇到问题:

1. 检查文件权限: `chmod -R u+rw api/ rag/ agent/`
2. 检查 Python 语法: `python -m py_compile api/apps/*.py`
3. 查看 Docker 镜像内容: `docker run --rm -it $DOCKER_IMAGE ls -la /ragflow/`

EOF

echo -e "${GREEN}✓ 报告已生成: $REPORT_FILE${NC}"

# 显示摘要
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 代码恢复完成!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}恢复目录:${NC} $RECOVERY_DIR"
echo -e "${YELLOW}恢复报告:${NC} $REPORT_FILE"
echo ""
echo -e "${BLUE}提取的内容:${NC}"
du -sh "$RECOVERY_DIR"/* 2>/dev/null | while read size path; do
    echo -e "  ${GREEN}$size${NC}  $(basename $path)"
done
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo -e "  1. 查看恢复报告: ${BLUE}cat $REPORT_FILE${NC}"
echo -e "  2. 对比差异: ${BLUE}diff -r $RECOVERY_DIR/api ./api${NC}"
echo -e "  3. 恢复代码: ${BLUE}cp -r $RECOVERY_DIR/api ./${NC}"
echo ""
echo -e "${GREEN}提示: 建议先对比差异,再决定如何恢复!${NC}"
echo ""

