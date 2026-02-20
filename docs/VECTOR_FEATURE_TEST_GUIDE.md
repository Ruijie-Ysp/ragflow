# 向量数据展示功能测试指南

## 当前状态

✅ **代码已通过 Docker Volume 挂载，无需重新构建镜像即可测试！**

已挂载的文件：
- 后端 API: `api/apps/api_app.py`, `api/apps/chunk_app.py`
- 前端组件: `web/src/components/vector-*.tsx`
- 前端 Hook: `web/src/hooks/use-vector-metadata.ts`
- 工具栏: `web/src/pages/add-knowledge/components/knowledge-chunk/components/chunk-toolbar/index.tsx`
- 模态框: `web/src/pages/add-knowledge/components/knowledge-chunk/components/vector-modal/`

## 快速测试步骤

### 1. 访问 RAGFlow

打开浏览器访问：
```
http://localhost
```

### 2. 登录系统

使用你的账号登录（如 `yang_sp@163.com`）

### 3. 进入知识库

1. 点击左侧菜单的"知识库"
2. 选择一个已有的知识库（或创建新的）
3. 上传一个文档（如果还没有）
4. 等待文档解析完成

### 4. 查看 Chunk 列表

1. 点击已解析的文档
2. 进入 Chunk 管理页面
3. 你应该能看到文档的所有 chunk

### 5. 打开向量数据查看器

在 Chunk 列表页面的工具栏中：
1. 找到**函数图标按钮** (fx) - 位于搜索按钮和过滤按钮之间
2. 点击该按钮
3. 应该会弹出"向量数据查看器"模态框

### 6. 查看向量数据

在模态框中：

#### 标签页 1: 向量统计
- 查看总体统计信息
- 检查向量覆盖率
- 查看平均范数、均值、标准差

#### 标签页 2: Chunk 列表
- 浏览所有 chunk
- 查看每个 chunk 的向量元数据
- 点击某个 chunk 查看详情

#### 标签页 3: 详细信息
- 查看选中 chunk 的完整向量信息
- 查看统计数据（维度、范数、均值、标准差、最小值、最大值）

### 7. 下载向量数据

1. 在模态框顶部，启用"包含完整向量"开关
2. 等待数据重新加载（会包含完整向量数组）
3. 点击"下载所有向量"按钮
4. 检查下载的 JSON 文件

## 测试检查点

### ✅ 前端功能测试

- [ ] 函数图标按钮是否显示在工具栏中
- [ ] 点击按钮是否弹出模态框
- [ ] 模态框是否包含三个标签页
- [ ] "向量统计"标签页是否显示统计信息
- [ ] "Chunk 列表"标签页是否显示所有 chunk
- [ ] 点击 chunk 是否切换到"详细信息"标签页
- [ ] "包含完整向量"开关是否工作
- [ ] "下载所有向量"按钮是否工作
- [ ] 下载的 JSON 文件格式是否正确

### ✅ 后端 API 测试

测试内部 API（需要登录 Token）：

```bash
# 获取登录 Token
TOKEN="你的登录Token"

# 测试不包含向量
curl -X POST http://localhost/api/chunk/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "doc_id": "你的文档ID",
    "page": 1,
    "size": 10,
    "include_vector": false
  }' | jq .

# 测试包含向量元数据
curl -X POST http://localhost/api/chunk/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "doc_id": "你的文档ID",
    "page": 1,
    "size": 10,
    "include_vector": true,
    "include_full_vector": false
  }' | jq .

# 测试包含完整向量
curl -X POST http://localhost/api/chunk/list \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "doc_id": "你的文档ID",
    "page": 1,
    "size": 10,
    "include_vector": true,
    "include_full_vector": true
  }' | jq .
```

检查点：
- [ ] `include_vector=false` 时，响应中没有 `vector_metadata` 字段
- [ ] `include_vector=true` 时，响应中有 `vector_metadata` 字段
- [ ] `vector_metadata` 包含：`dimension`, `field_name`, `mean`, `std`, `min`, `max`, `norm`
- [ ] `include_full_vector=true` 时，`vector_metadata` 包含 `vector` 数组
- [ ] `vector` 数组长度等于 `dimension`

### ✅ 数据验证

检查向量元数据的合理性：

- [ ] 向量维度通常为 1024（取决于 embedding 模型）
- [ ] 向量范数通常在 10-30 之间
- [ ] 均值通常接近 0
- [ ] 标准差通常在 0.3-0.6 之间
- [ ] 最小值和最大值在合理范围内（通常 -3 到 3）

## 常见问题排查

### 问题 1: 函数图标按钮不显示

**可能原因**：
- 前端代码未正确挂载
- 浏览器缓存

**解决方案**：
```bash
# 检查文件是否挂载
docker exec ragflow-server ls -la /ragflow/web/src/pages/add-knowledge/components/knowledge-chunk/components/chunk-toolbar/index.tsx

# 清除浏览器缓存，强制刷新（Cmd+Shift+R 或 Ctrl+Shift+R）
```

### 问题 2: 点击按钮没有反应

**可能原因**：
- 前端组件未正确挂载
- JavaScript 错误

**解决方案**：
```bash
# 打开浏览器开发者工具（F12）
# 查看 Console 标签页是否有错误

# 检查组件文件是否挂载
docker exec ragflow-server ls -la /ragflow/web/src/pages/add-knowledge/components/knowledge-chunk/components/vector-modal/
```

### 问题 3: 模态框显示但没有数据

**可能原因**：
- 后端 API 未正确挂载
- 文档没有向量数据

**解决方案**：
```bash
# 检查后端文件是否挂载
docker exec ragflow-server ls -la /ragflow/api/apps/chunk_app.py

# 查看后端日志
docker logs ragflow-server --tail 100

# 确认文档已完成解析和向量化
```

### 问题 4: API 返回错误

**可能原因**：
- Python 语法错误
- 缺少依赖

**解决方案**：
```bash
# 查看后端日志
docker logs ragflow-server --tail 100 | grep -i error

# 重启容器
cd docker
docker compose restart ragflow
```

## 修改代码后的测试流程

由于使用了 Volume 挂载，你可以：

1. **修改本地代码**
   - 编辑 `api/apps/api_app.py` 或其他文件
   - 保存文件

2. **重启后端服务**（仅后端代码修改需要）
   ```bash
   docker compose restart ragflow
   ```

3. **刷新浏览器**（前端代码修改）
   - 按 `Cmd+Shift+R`（Mac）或 `Ctrl+Shift+R`（Windows/Linux）
   - 强制刷新，清除缓存

4. **重新测试**
   - 无需重新构建镜像！

## 性能测试

### 测试大文档

1. 上传一个大文档（100+ 页）
2. 等待解析完成
3. 打开向量数据查看器
4. 记录加载时间

**预期**：
- 50 个 chunk 的元数据加载时间 < 1 秒
- 50 个 chunk 的完整向量加载时间 < 3 秒

### 测试并发

在多个浏览器标签页中同时打开向量数据查看器，检查是否有性能问题。

## 测试完成后

如果测试通过，你可以：

1. **继续使用 Volume 挂载**（开发模式）
   - 优点：修改代码无需重新构建
   - 缺点：性能略低于原生镜像

2. **重新构建镜像**（生产模式）
   ```bash
   docker build --build-arg LIGHTEN=1 -f Dockerfile \
     -t infiniflow/ragflow:v0.21-custom-arm64 .
   
   # 移除 docker-compose.yml 中的 volume 挂载
   # 重启容器
   cd docker
   docker compose down
   docker compose up -d
   ```

## 反馈

测试过程中如有任何问题，请记录：
- 问题描述
- 复现步骤
- 错误信息（截图或日志）
- 浏览器和版本
- 操作系统

祝测试顺利！🎉

