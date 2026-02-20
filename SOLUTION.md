# BrowserOS MCP Server 连接问题 - 最终解决方案

## ✅ 测试结果

我已经通过 Python 脚本测试确认：

**BrowserOS MCP Server 完全不需要认证！**

```
✅ 成功获取 29 个工具
✅ 所有 header 组合都能成功连接（无 headers、空 Authorization、Bearer Token 等）
✅ MCP Python SDK 工作正常
```

## 🔍 问题根源

根据您的错误日志：
```
Test MCP error: Connection failed: ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
```

真正的错误是 **ExceptionGroup** 包装的 **ConnectError**：
```
ConnectError: [Errno 8] nodename nor servname provided, or not known
```

这意味着：**`host.docker.internal` 无法解析！**

**为什么会这样？**

`host.docker.internal` 是 Docker 内部的特殊域名，**只在 Docker 容器内部有效**。

但是，RAGFlow 的测试请求可能是从宿主机发起的（通过浏览器），而不是从 Docker 容器内部发起的！

**解决方案**：需要根据请求来源使用不同的 URL

## 🎯 正确的配置方法

### 步骤 1: 确认 BrowserOS 正在运行

```bash
# 检查端口 9101 是否被监听
lsof -i :9101

# 或者
netstat -an | grep 9101
```

应该看到类似输出：
```
LISTEN      *:9101
```

### 步骤 2: 测试从宿主机连接

```bash
curl -X POST http://127.0.0.1:9101/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"initialize",
    "params":{
      "protocolVersion":"2024-11-05",
      "capabilities":{},
      "clientInfo":{"name":"test","version":"1.0"}
    }
  }'
```

应该返回 200 OK 和 JSON 响应。

### 步骤 3: 在 RAGFlow 中正确配置

**重要：根据您的环境选择正确的 URL**

#### 方案 A: 使用宿主机 IP（推荐）

获取宿主机 IP：
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1

# 或者
ipconfig getifaddr en0  # macOS WiFi
```

假设您的宿主机 IP 是 `192.168.1.100`，在 RAGFlow 中配置：

1. **Name**: `BrowserOS`
2. **URL**: `http://192.168.1.100:9101/mcp`  ⚠️ **使用您的实际 IP！**
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空** ⚠️ **不需要填写！**

#### 方案 B: 使用 host.docker.internal（可能不工作）

如果您的 Docker 版本支持 `host.docker.internal`：

1. **Name**: `BrowserOS`
2. **URL**: `http://host.docker.internal:9101/mcp`
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空**

**注意**：这个方案可能会失败，因为测试请求是从浏览器（宿主机）发起的，而不是从 Docker 容器内部发起的。

### 步骤 4: 应用修复并重启

```bash
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow
./restart_ragflow_with_mcp_fix.sh
```

这会应用改进的错误信息，帮助您更好地诊断问题。

### 步骤 5: 测试连接

点击 RAGFlow 中的测试按钮（刷新图标）。

**预期结果**:
- ✅ 成功: "Connected · 29 tools available"
- ❌ 失败: 查看详细错误信息（现在会更准确）

## 🐛 如果仍然失败

### 检查 1: Docker 网络配置

确认 `docker-compose.yml` 中有 `extra_hosts` 配置：

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### 检查 2: 从 Docker 容器内测试

如果 Docker 命令可用：

```bash
# 进入 RAGFlow 容器
docker exec -it ragflow-server bash

# 在容器内测试
curl -v http://host.docker.internal:9101/mcp
```

### 检查 3: 使用宿主机 IP

如果 `host.docker.internal` 不工作，使用宿主机的实际 IP：

```bash
# 获取宿主机 IP
ifconfig | grep "inet " | grep -v 127.0.0.1
```

然后在 RAGFlow 中使用：
```
http://192.168.x.x:9101/mcp
```

### 检查 4: 查看详细日志

```bash
cd docker
docker compose logs -f ragflow-server | grep -i mcp
```

现在错误信息会显示：
- 具体的错误类型（ConnectError, Timeout, 401, 403 等）
- 针对性的解决建议

## 📊 常见错误及解决方案

### 错误 1: Connection refused

**原因**: 无法连接到 BrowserOS

**解决方案**:
1. 确认 BrowserOS 正在运行
2. 使用 `host.docker.internal` 而不是 `127.0.0.1`
3. 检查防火墙设置

### 错误 2: 406 Not Acceptable

**原因**: MCP SDK 的 bug（已在最新版本修复）

**解决方案**:
- 这个错误不应该出现，因为 MCP SDK 会自动设置正确的 Accept header
- 如果出现，请更新 MCP SDK

### 错误 3: Timeout

**原因**: 网络连接慢或 BrowserOS 响应慢

**解决方案**:
1. 增加 timeout 值（默认 10 秒）
2. 检查网络连接
3. 重启 BrowserOS

## 🎉 成功标志

当您看到以下内容时，说明配置成功：

```
✅ Connected · 29 tools available
```

可用的工具包括：
- `list_console_messages` - 列出控制台消息
- `list_network_requests` - 列出网络请求
- `browser_type_text` - 在输入框中输入文本
- `browser_click_element` - 点击元素
- `browser_navigate` - 导航到 URL
- ... 等 29 个工具

## 💡 关键要点

1. **BrowserOS MCP Server 不需要认证** ✅
2. **必须使用 `host.docker.internal`** (Docker 环境) ✅
3. **Server Type 选择 `streamable-http`** ✅
4. **Authorization Token 留空** ✅
5. **URL 必须是 `/mcp` 结尾** ✅

## 🔧 调试工具

我已经创建了以下工具帮助您诊断：

1. **test_browseros_connection.py** - Python 测试脚本
   ```bash
   python3 test_browseros_connection.py
   ```

2. **diagnose_browseros_mcp.sh** - 诊断脚本
   ```bash
   ./diagnose_browseros_mcp.sh
   ```

3. **test_browseros_mcp_auth.sh** - 认证测试脚本
   ```bash
   ./test_browseros_mcp_auth.sh
   ```

## 📝 完整配置示例

### RAGFlow MCP 配置

```json
{
  "name": "BrowserOS",
  "url": "http://host.docker.internal:9101/mcp",
  "server_type": "streamable-http",
  "timeout": 10
}
```

**注意**: 不需要 `headers` 或 `authorization_token` 字段！

## 🚀 下一步

1. 确认 BrowserOS 正在运行
2. 使用正确的 URL: `http://host.docker.internal:9101/mcp`
3. Server Type: `streamable-http`
4. **不要填写** Authorization Token
5. 点击测试
6. 如果失败，查看改进后的错误信息

---

**如果按照以上步骤操作后仍然失败，请提供：**
1. 改进后的详细错误信息
2. `lsof -i :9101` 的输出
3. RAGFlow 日志中的 MCP 相关信息

这将帮助我们进一步诊断问题。

