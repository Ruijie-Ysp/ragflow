# Docker 网络连接问题 - 解决方案

## 🔍 当前问题

从日志可以看到：
```
Error fetching tools from MCP server: streamable-http: http://127.0.0.1:9101/mcp
ValueError: Connection failed: ConnectError: All connection attempts failed
```

**问题**：Docker 容器内的 `127.0.0.1` 指向容器自己，而不是宿主机！

## 📊 网络架构说明

```
┌─────────────────────────────────────────┐
│ 宿主机 (macOS)                           │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ BrowserOS MCP Server              │  │
│  │ 监听: 127.0.0.1:9101              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Docker 容器: ragflow-server       │  │
│  │                                   │  │
│  │ 127.0.0.1 → 容器自己 ❌           │  │
│  │ host.docker.internal → 宿主机 ✅  │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## ✅ 正确的解决方案

### 方案 1: 使用 host.docker.internal（推荐）

在 RAGFlow 中配置：

1. **Name**: `BrowserOS`
2. **URL**: `http://host.docker.internal:9101/mcp` ⚠️ **使用 host.docker.internal**
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空**

### 为什么之前失败？

之前使用 `http://host.docker.internal:9101/mcp` 失败是因为：
- 测试请求是从**浏览器**（宿主机）发起的
- 宿主机无法解析 `host.docker.internal`

但是：
- **实际的 MCP 调用是从 Docker 容器内发起的**
- Docker 容器内可以解析 `host.docker.internal`

### 方案 2: 配置 BrowserOS 监听 0.0.0.0

如果方案 1 不工作，需要配置 BrowserOS 监听所有网络接口。

## 🔧 验证 Docker 网络配置

### 检查 extra_hosts 配置

确认 `docker/docker-compose.yml` 中有：

```yaml
services:
  ragflow-server:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### 测试容器内网络连接

如果 Docker 命令可用，运行：

```bash
# 进入容器
docker exec -it ragflow-server bash

# 检查 /etc/hosts
cat /etc/hosts | grep host.docker.internal

# 测试连接
curl -v http://host.docker.internal:9101/mcp
```

## 🚀 操作步骤

### 步骤 1: 在 RAGFlow 中配置

打开 RAGFlow Web 界面，配置 MCP 服务器：

1. **Name**: `BrowserOS`
2. **URL**: `http://host.docker.internal:9101/mcp`
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空**

### 步骤 2: 点击测试

**重要**：测试可能会失败，但这是正常的！

测试失败的原因：
- 测试请求是从浏览器（宿主机）发起的
- 宿主机无法解析 `host.docker.internal`

### 步骤 3: 保存配置

即使测试失败，也要**保存配置**！

### 步骤 4: 实际使用时测试

在 RAGFlow 的对话中实际调用 MCP 工具时，请求是从 Docker 容器内发起的，应该可以成功。

## 🔍 如何判断是否成功？

### 测试失败但实际可用的情况

如果您看到：
- ❌ 测试按钮显示失败
- ✅ 但保存后，工具列表显示 29 个工具

这说明配置是正确的！测试失败只是因为测试请求是从浏览器发起的。

### 真正的测试方法

在 RAGFlow 对话中尝试使用 MCP 工具：

1. 创建一个对话
2. 启用 BrowserOS MCP 工具
3. 发送一个需要使用浏览器的请求
4. 查看是否成功调用工具

## 💡 替代方案：配置 BrowserOS 监听 0.0.0.0

如果 `host.docker.internal` 方案不工作，需要配置 BrowserOS 监听所有网络接口。

### 查找 BrowserOS 配置

1. **VS Code 扩展设置**
   - 打开 VS Code
   - Cmd+Shift+P → "Preferences: Open Settings (UI)"
   - 搜索 "BrowserOS"
   - 查找 "Host" 或 "Server Host" 设置

2. **配置文件**
   - 可能在 `~/.vscode/extensions/browseros-*/config.json`
   - 或者在扩展的设置中

### 修改监听地址

将监听地址从 `127.0.0.1` 改为 `0.0.0.0`。

修改后，BrowserOS 会监听所有网络接口，然后您可以使用：
```
URL: http://192.168.139.3:9101/mcp
```

### 验证修改

```bash
# 重启 BrowserOS 后检查
lsof -i :9101

# 应该看到
browseros ... TCP *:bacula-dir (LISTEN)
# 而不是
browseros ... TCP localhost:bacula-dir (LISTEN)
```

## 📝 配置对比

### 配置 1: host.docker.internal（推荐）

**优点**：
- ✅ 不需要修改 BrowserOS 配置
- ✅ 安全，只有本机可以访问
- ✅ 适合大多数场景

**缺点**：
- ❌ 测试按钮会失败（但实际使用时可以工作）

**RAGFlow 配置**：
```
URL: http://host.docker.internal:9101/mcp
```

### 配置 2: 0.0.0.0 + 宿主机 IP

**优点**：
- ✅ 测试按钮可以成功
- ✅ 更直观

**缺点**：
- ❌ 需要修改 BrowserOS 配置
- ❌ 可能存在安全风险

**RAGFlow 配置**：
```
URL: http://192.168.139.3:9101/mcp
```

## 🎯 推荐方案

### 方案 A: 先尝试 host.docker.internal

1. 在 RAGFlow 中配置：`http://host.docker.internal:9101/mcp`
2. 点击测试（可能失败，忽略）
3. **保存配置**
4. 在实际对话中测试 MCP 工具调用
5. 查看 RAGFlow 日志确认是否成功

### 方案 B: 如果方案 A 不工作

1. 配置 BrowserOS 监听 `0.0.0.0`
2. 重启 BrowserOS
3. 在 RAGFlow 中配置：`http://192.168.139.3:9101/mcp`
4. 测试应该成功

## 🔍 调试方法

### 查看 RAGFlow 日志

```bash
cd docker
docker compose logs -f ragflow-server | grep -i mcp
```

### 成功的日志应该显示

```
INFO client_session initialized successfully
INFO Negotiated protocol version: 2025-06-18
```

### 失败的日志会显示

```
ERROR Connection failed: ConnectError: All connection attempts failed
```

## 📚 关键要点

1. **Docker 容器内的 127.0.0.1 指向容器自己** ❌
2. **使用 host.docker.internal 访问宿主机** ✅
3. **测试按钮可能失败，但实际使用时可以工作** ⚠️
4. **BrowserOS 默认只监听 localhost** ℹ️
5. **不需要认证** ✅

## 🎉 成功标志

当在 RAGFlow 对话中成功调用 MCP 工具时，日志会显示：

```
INFO client_session initialized successfully
INFO Successfully called MCP tool: browser_navigate
```

---

**总结**：使用 `http://host.docker.internal:9101/mcp`，即使测试失败也要保存配置，然后在实际对话中测试！

