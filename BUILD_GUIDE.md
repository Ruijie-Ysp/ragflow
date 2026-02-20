# RAGFlow Docker 镜像构建指南

## 🚀 快速开始

### 方法1: 使用构建脚本(推荐)

```bash
# 在项目根目录执行
./build_docker_image.sh
```

这个脚本会:
- ✅ 自动检查 Docker 环境
- ✅ 可选清理构建缓存
- ✅ 构建镜像并保存日志
- ✅ 显示下一步操作指引

### 方法2: 手动构建

```bash
# 基础构建命令
docker build \
    --build-arg LIGHTEN=1 \
    -f Dockerfile \
    -t infiniflow/ragflow:0.21-arm-new \
    --progress=plain \
    .
```

## 📋 构建前检查清单

- [ ] Docker 已启动并运行正常
- [ ] 磁盘空间充足 (至少 10GB 可用空间)
- [ ] 网络连接正常
- [ ] 代码已更新到最新版本

## 🔧 Dockerfile 优化说明

### 前端编译优化

已在 Dockerfile 中添加了以下优化:

1. **使用 `--legacy-peer-deps`**: 避免依赖冲突
2. **失败重试机制**: 如果首次构建失败,会自动清理缓存并重试
3. **详细日志输出**: 便于排查问题

相关代码(第164-179行):
```dockerfile
COPY web web
COPY docs docs
# Install frontend dependencies and build
# Use --legacy-peer-deps to avoid dependency conflicts
# Clear npm cache if build fails
RUN --mount=type=cache,id=ragflow_npm,target=/root/.npm,sharing=locked \
    cd web && \
    echo "Installing frontend dependencies..." && \
    npm install --legacy-peer-deps && \
    echo "Building frontend..." && \
    npm run build || \
    (echo "Build failed, clearing cache and retrying..." && \
     npm cache clean --force && \
     rm -rf node_modules && \
     npm install --legacy-peer-deps && \
     npm run build)
```

## 🐛 常见问题排查

### 问题1: 前端编译失败

**症状**: 构建过程中出现 `Module not found` 或 `webpack compiled with errors`

**解决方案**:
1. 清理 Docker 构建缓存:
   ```bash
   docker builder prune -f
   ```

2. 重新构建:
   ```bash
   ./build_docker_image.sh
   ```

### 问题2: 网络超时

**症状**: `npm install` 时出现超时错误

**解决方案**:
1. 使用国内镜像源构建:
   ```bash
   docker build \
       --build-arg LIGHTEN=1 \
       --build-arg NEED_MIRROR=1 \
       -f Dockerfile \
       -t infiniflow/ragflow:0.21-arm-new \
       .
   ```

### 问题3: 磁盘空间不足

**症状**: `no space left on device`

**解决方案**:
1. 清理未使用的 Docker 资源:
   ```bash
   docker system prune -a --volumes
   ```

2. 检查磁盘空间:
   ```bash
   df -h
   ```

## 📦 构建后操作

### 1. 验证镜像

```bash
# 查看镜像信息
docker images infiniflow/ragflow:0.21-arm-new

# 查看镜像详细信息
docker inspect infiniflow/ragflow:0.21-arm-new
```

### 2. 更新 docker-compose 配置

编辑 `docker/.env` 文件:

```bash
# 修改镜像名称
RAGFLOW_IMAGE=infiniflow/ragflow:0.21-arm-new
```

### 3. 重启服务

```bash
cd docker
docker compose down
docker compose up -d
```

### 4. 验证服务

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f ragflow

# 访问服务
curl http://127.0.0.1
```

## 🔍 构建日志分析

构建日志保存在 `docker_build.log` 文件中。

### 关键检查点

1. **Python 依赖安装**:
   ```
   uv sync --python 3.10 --frozen
   ```

2. **前端依赖安装**:
   ```
   Installing frontend dependencies...
   npm install --legacy-peer-deps
   ```

3. **前端编译**:
   ```
   Building frontend...
   npm run build
   ```

4. **镜像构建完成**:
   ```
   Successfully tagged infiniflow/ragflow:0.21-arm-new
   ```

## 📊 构建参数说明

### LIGHTEN

- `LIGHTEN=1`: 构建轻量版(不包含嵌入模型,推荐)
- `LIGHTEN=0`: 构建完整版(包含嵌入模型,镜像较大)

### NEED_MIRROR

- `NEED_MIRROR=0`: 使用官方源(默认,国外网络)
- `NEED_MIRROR=1`: 使用国内镜像源(国内网络)

## 🎯 最佳实践

### 1. 定期清理

```bash
# 每周清理一次未使用的资源
docker system prune -f

# 每月清理一次构建缓存
docker builder prune -f
```

### 2. 版本管理

```bash
# 使用有意义的标签
docker build -t infiniflow/ragflow:0.21-$(date +%Y%m%d) .

# 保留多个版本
docker tag infiniflow/ragflow:0.21-20251106 infiniflow/ragflow:latest
```

### 3. 构建优化

```bash
# 使用 BuildKit 加速构建
export DOCKER_BUILDKIT=1

# 并行构建多个平台
docker buildx build --platform linux/amd64,linux/arm64 -t infiniflow/ragflow:0.21-multi .
```

## 📝 构建时间参考

在不同硬件配置下的预估构建时间:

| 配置 | 首次构建 | 增量构建 |
|------|---------|---------|
| M1 Mac (8核) | 15-20分钟 | 5-8分钟 |
| M2 Mac (10核) | 12-15分钟 | 4-6分钟 |
| Intel i7 (8核) | 20-25分钟 | 8-10分钟 |

*注: 实际时间取决于网络速度和磁盘性能*

## 🆘 获取帮助

如果遇到问题:

1. 查看构建日志: `cat docker_build.log`
2. 检查 Docker 状态: `docker info`
3. 查看系统资源: `docker stats`
4. 提交 Issue: [GitHub Issues](https://github.com/infiniflow/ragflow/issues)

## ✅ 验证清单

构建完成后,请验证以下内容:

- [ ] 镜像构建成功
- [ ] 镜像大小合理 (轻量版约 3-4GB)
- [ ] 容器能正常启动
- [ ] 前端页面能正常访问
- [ ] 语料库页面显示正常
- [ ] 设置页面显示正常
- [ ] 数据库配置功能正常

---

**最后更新**: 2025-11-06  
**版本**: v1.0

