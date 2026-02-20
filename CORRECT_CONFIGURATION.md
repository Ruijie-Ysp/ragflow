# BrowserOS MCP Server - 正确配置方法

## 🔍 问题诊断结果

通过日志和测试，我发现了真正的问题：

### BrowserOS 只监听 localhost

```bash
$ lsof -i :9101
browseros 53255 ... TCP localhost:bacula-dir (LISTEN)
```

这意味着：
- ✅ `http://127.0.0.1:9101/mcp` - 可以访问
- ❌ `http://192.168.139.3:9101/mcp` - Connection refused

### 测试结果

```bash
# 测试 127.0.0.1 - 成功
$ curl http://127.0.0.1:9101/mcp
HTTP/1.1 200 OK ✅

# 测试 192.168.139.3 - 失败
$ curl http://192.168.139.3:9101/mcp
Connection refused ❌
```

## ✅ 正确的配置方法

### 在 RAGFlow 中使用 127.0.0.1

由于 RAGFlow 在 Docker 容器内运行，并且 Docker Compose 配置了 `extra_hosts`，容器可以访问宿主机的 localhost。

**在 RAGFlow Web 界面中配置**：

1. **Name**: `BrowserOS`
2. **URL**: `http://127.0.0.1:9101/mcp` ⚠️ **使用 127.0.0.1**
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空**

### 为什么这样可以工作？

RAGFlow 的 Docker Compose 配置中有：

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

这使得：
- Docker 容器内的网络请求可以访问宿主机
- 容器内访问 `127.0.0.1` 会被路由到宿主机的 `127.0.0.1`
- BrowserOS 监听在宿主机的 `127.0.0.1:9101`
- 因此 RAGFlow 可以通过 `http://127.0.0.1:9101/mcp` 访问 BrowserOS

## 🔧 替代方案：配置 BrowserOS 监听所有接口

如果您想让 BrowserOS 可以从网络上的其他机器访问，需要配置它监听 `0.0.0.0` 而不是 `127.0.0.1`。

### 查找 BrowserOS 配置

BrowserOS 的配置可能在以下位置：

1. **VS Code 扩展设置**
   - 打开 VS Code
   - 进入设置 (Cmd+,)
   - 搜索 "BrowserOS"
   - 查找 "Host" 或 "Listen Address" 设置

2. **配置文件**
   - 可能在 `~/.browseros/config.json`
   - 或者在 VS Code 的扩展数据目录

3. **启动参数**
   - 如果是通过命令行启动，检查启动脚本

### 修改监听地址

将监听地址从 `127.0.0.1` 改为 `0.0.0.0`：

```json
{
  "host": "0.0.0.0",
  "port": 9101
}
```

**注意**：这会让 BrowserOS 可以从网络上的任何机器访问，可能存在安全风险。

## 📊 配置对比

### 方案 1: 使用 127.0.0.1（推荐）

**优点**：
- ✅ 简单，不需要修改 BrowserOS 配置
- ✅ 安全，只有本机可以访问
- ✅ 适合大多数场景

**缺点**：
- ❌ 只能在同一台机器上使用

**RAGFlow 配置**：
```
URL: http://127.0.0.1:9101/mcp
```

### 方案 2: 配置 BrowserOS 监听 0.0.0.0

**优点**：
- ✅ 可以从网络上的其他机器访问
- ✅ 更灵活

**缺点**：
- ❌ 需要修改 BrowserOS 配置
- ❌ 可能存在安全风险
- ❌ 需要配置防火墙

**RAGFlow 配置**：
```
URL: http://192.168.139.3:9101/mcp
```

## 🚀 立即操作

### 步骤 1: 在 RAGFlow 中重新配置

打开 RAGFlow Web 界面，修改 MCP 服务器配置：

1. **Name**: `BrowserOS`
2. **URL**: `http://127.0.0.1:9101/mcp` ⚠️ **改为 127.0.0.1**
3. **Server Type**: `streamable-http`
4. **Authorization Token**: **留空**

### 步骤 2: 测试连接

点击测试按钮（刷新图标）。

**预期结果**：
```
✅ Connected · 29 tools available
```

### 步骤 3: 如果还是失败

查看 RAGFlow 日志：

```bash
cd docker
docker compose logs -f ragflow-server | grep -i mcp
```

现在错误信息会更详细，帮助您快速定位问题。

## 🔍 验证 Docker 网络配置

如果使用 `127.0.0.1` 仍然失败，检查 Docker 网络配置：

```bash
# 进入 RAGFlow 容器
docker exec -it ragflow-server bash

# 在容器内测试连接宿主机
curl -v http://host.docker.internal:9101/mcp
curl -v http://127.0.0.1:9101/mcp

# 检查 /etc/hosts
cat /etc/hosts | grep host.docker.internal
```

应该看到：
```
192.168.65.254  host.docker.internal
```

## 💡 关键要点

1. **BrowserOS 只监听 127.0.0.1** ✅
2. **在 RAGFlow 中使用 http://127.0.0.1:9101/mcp** ✅
3. **不要使用 192.168.x.x**（BrowserOS 不监听这些接口）❌
4. **不需要认证** ✅
5. **Server Type 选择 streamable-http** ✅

## 📝 完整配置示例

```json
{
  "name": "BrowserOS",
  "url": "http://127.0.0.1:9101/mcp",
  "server_type": "streamable-http"
}
```

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

---

## 🔧 故障排除

### 错误 1: Connection refused

**原因**：使用了错误的 IP 地址（如 192.168.x.x）

**解决**：改用 `http://127.0.0.1:9101/mcp`

### 错误 2: Connection timeout

**原因**：Docker 网络配置问题

**解决**：
1. 检查 `docker-compose.yml` 中的 `extra_hosts` 配置
2. 重启 Docker 服务
3. 在容器内测试 `host.docker.internal`

### 错误 3: No tools available

**原因**：BrowserOS 未正常运行

**解决**：
1. 检查 BrowserOS 是否在运行：`lsof -i :9101`
2. 重启 BrowserOS 扩展
3. 查看 BrowserOS 日志

---

**总结**：使用 `http://127.0.0.1:9101/mcp` 而不是 `http://192.168.139.3:9101/mcp`！

