# RAGFlow MCP 服务器添加错误修复

## 📋 问题描述

在 RAGFlow 中添加 BrowserOS MCP 服务器时，即使连接失败也会创建一个没有工具的 MCP 服务器记录，而不是返回明确的错误信息。

### 错误表现

```
用户添加 MCP 服务器 → 连接失败 → 创建了空工具列表的服务器 ❌
```

### 期望行为

```
用户添加 MCP 服务器 → 连接失败 → 显示明确的错误信息 ✅
```

## 🔍 根本原因

### Bug 位置 1: `api/utils/api_utils.py`

```python
# 修复前
try:
    tools = tool_call_session.get_tools(timeout)
except Exception:
    tools = []  # ⚠️ 异常被吞掉，没有记录错误

# ...
return results, ""  # ⚠️ 即使失败也返回空的 err_message
```

### Bug 位置 2: `api/apps/mcp_server_app.py`

```python
# 修复前
server_tools, err_message = get_mcp_tools([mcp_server], timeout)
if err_message:
    return get_data_error_result(err_message)

tools = server_tools[server_name]  # ⚠️ 如果 tools 为空列表，这里不会报错
tools = {}  # ⚠️ 转换为空字典
variables["tools"] = tools  # ⚠️ 保存了空工具列表
```

## ✅ 修复内容

### 1. 改进 `get_mcp_tools()` 错误处理

**文件**: `api/utils/api_utils.py`

**修改内容**:
- 添加 `errors` 列表收集所有错误信息
- 在捕获异常时记录详细的错误信息
- 如果有错误，返回错误信息而不是空字符串

```python
def get_mcp_tools(mcp_servers: list, timeout: float | int = 10) -> tuple[dict, str]:
    results = {}
    tool_call_sessions = []
    errors = []  # ✅ 新增：收集错误信息
    
    try:
        for mcp_server in mcp_servers:
            server_key = mcp_server.id
            # ...
            try:
                tools = tool_call_session.get_tools(timeout)
            except Exception as e:
                # ✅ 记录错误而不是静默忽略
                error_msg = f"Failed to get tools from MCP server '{server_key}': {str(e)}"
                logging.error(error_msg)
                errors.append(error_msg)
                tools = []
            # ...
        
        # ✅ 如果有错误，返回错误信息
        if errors:
            return results, "; ".join(errors)
        
        return results, ""
```

### 2. 改进 API 验证逻辑

**文件**: `api/apps/mcp_server_app.py`

**修改内容**:
- 在 `/create` API 中添加工具列表验证
- 在 `/update` API 中添加工具列表验证
- 在 `/import` API 中添加工具列表验证

```python
server_tools, err_message = get_mcp_tools([mcp_server], timeout)
if err_message:
    return get_data_error_result(err_message)

# ✅ 检查是否获取到工具
if server_name not in server_tools:
    return get_data_error_result(f"Failed to retrieve tools from MCP server '{server_name}'")

tools = server_tools[server_name]
# ✅ 检查工具列表是否为空
if not tools:
    return get_data_error_result(f"No tools available from MCP server '{server_name}'. Please check if the server is running correctly.")
```

## 🚀 如何应用修复

### 方法 1: 使用提供的脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x restart_ragflow_with_mcp_fix.sh

# 运行脚本
./restart_ragflow_with_mcp_fix.sh
```

### 方法 2: 手动重启

```bash
# 进入 docker 目录
cd docker

# 停止 RAGFlow 服务器
docker compose stop ragflow-server

# 启动 RAGFlow 服务器（会自动挂载修改的文件）
docker compose up -d ragflow-server

# 查看日志确认启动成功
docker compose logs -f ragflow-server
```

## 🧪 测试修复

### 测试场景 1: 连接失败（BrowserOS 未运行）

1. **停止 BrowserOS MCP Server**（如果正在运行）
2. **尝试添加 MCP 服务器**:
   - URL: `http://127.0.0.1:9101/mcp`
   - Server Type: `streamable-http`
3. **预期结果**: 
   ```
   ❌ Failed to get tools from MCP server 'xxx': Connection failed (possibly due to auth error). Please check authentication settings first
   ```

### 测试场景 2: 连接成功（BrowserOS 运行中）

1. **启动 BrowserOS MCP Server**
2. **尝试添加 MCP 服务器**:
   - URL: `http://127.0.0.1:9101/mcp`
   - Server Type: `streamable-http`
3. **预期结果**: 
   ```
   ✅ Connected · 29 tools available
   ```

### 测试场景 3: 更新现有服务器

1. **修改现有 MCP 服务器的 URL** 为无效地址
2. **预期结果**: 返回错误而不是更新为空工具列表

## 📁 修改的文件

1. **`api/utils/api_utils.py`**
   - 改进 `get_mcp_tools()` 函数的错误处理
   - 添加错误信息收集和返回

2. **`api/apps/mcp_server_app.py`**
   - 改进 `/create` API 的验证逻辑
   - 改进 `/update` API 的验证逻辑
   - 改进 `/import` API 的验证逻辑

3. **`docker/docker-compose.yml`**
   - 添加 volume 挂载以应用修复

## 📊 修复效果对比

### 修复前

```
连接失败 → 异常被吞掉 → 创建空工具的服务器 → 用户困惑 ❌
```

### 修复后

```
连接失败 → 记录错误 → 返回明确错误信息 → 用户知道问题所在 ✅
```

## 🔍 查看日志

```bash
# 实时查看日志
cd docker
docker compose logs -f ragflow-server

# 查看最近 100 行日志
docker compose logs --tail=100 ragflow-server

# 搜索 MCP 相关日志
docker compose logs ragflow-server | grep -i mcp
```

## 💡 额外建议

1. **添加连接超时提示**: 当前超时时间是 10 秒，可以在前端显示进度
2. **添加重试机制**: 对于临时网络问题，可以自动重试
3. **改进错误信息**: 区分不同类型的错误（连接失败、认证失败、超时等）
4. **添加健康检查**: 定期检查已保存的 MCP 服务器是否仍然可用

## 🐛 如果遇到问题

### 问题 1: 修改没有生效

**解决方案**:
```bash
# 确认 volume 挂载是否正确
docker compose config | grep -A 10 volumes

# 重新创建容器
cd docker
docker compose down ragflow-server
docker compose up -d ragflow-server
```

### 问题 2: 容器启动失败

**解决方案**:
```bash
# 查看详细错误日志
docker compose logs ragflow-server

# 检查文件权限
ls -la ../api/utils/api_utils.py
ls -la ../api/apps/mcp_server_app.py
```

### 问题 3: 仍然看到旧的错误行为

**解决方案**:
```bash
# 清除浏览器缓存
# 或者使用无痕模式访问

# 确认容器内的文件已更新
docker compose exec ragflow-server cat /ragflow/api/utils/api_utils.py | grep "errors = \[\]"
```

## 📞 支持

如果遇到任何问题，请检查:
1. Docker 容器是否正常运行
2. Volume 挂载是否正确配置
3. 文件路径是否正确
4. 日志中是否有错误信息

---

**修复完成时间**: 2025-10-30  
**修复版本**: RAGFlow 0.21  
**测试状态**: ✅ 已验证

