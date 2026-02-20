# BrowserOS MCP Server 连接故障排除指南

## 🔴 当前问题

**错误信息**: `Connection failed (possibly due to auth error). Please check authentication settings first`

**可能原因**:
1. BrowserOS MCP Server 需要认证（最可能）
2. BrowserOS MCP Server 未运行
3. URL 或端口配置错误
4. Docker 网络问题

## 🔍 诊断步骤

### 步骤 1: 确认 BrowserOS MCP Server 正在运行

```bash
# 运行诊断脚本
./diagnose_browseros_mcp.sh
```

**预期结果**: 端口 9101 应该被监听

### 步骤 2: 测试认证要求

```bash
# 运行认证测试脚本
./test_browseros_mcp_auth.sh
```

这个脚本会测试不同的认证方式，帮助您确定需要哪种认证。

### 步骤 3: 检查 BrowserOS 配置

1. **打开 BrowserOS 扩展设置**
2. **查找以下信息**:
   - API Key / Token
   - Authentication 设置
   - Server Port (确认是 9101)
   - Server Type (SSE 或 Streamable HTTP)

## ✅ 解决方案

### 方案 1: 添加认证 Header (最可能)

BrowserOS MCP Server 很可能需要认证。在 RAGFlow 中添加 MCP 服务器时：

#### 使用 Bearer Token

1. 在 BrowserOS 设置中找到 API Token
2. 在 RAGFlow 添加 MCP 服务器界面：
   - **URL**: `http://127.0.0.1:9101/mcp` (或 `http://host.docker.internal:9101/mcp`)
   - **Server Type**: `streamable-http`
   - **Headers**: 点击展开，添加:
     ```json
     {
       "Authorization": "Bearer YOUR_TOKEN_HERE"
     }
     ```

#### 使用 API Key

如果 BrowserOS 使用 API Key：

```json
{
  "X-API-Key": "YOUR_API_KEY_HERE"
}
```

或者：

```json
{
  "Authorization": "YOUR_API_KEY_HERE"
}
```

### 方案 2: 使用正确的 URL

#### 从宿主机访问

如果您在宿主机上测试：
```
http://127.0.0.1:9101/mcp
```

#### 从 Docker 容器访问

如果 RAGFlow 在 Docker 中运行，使用：
```
http://host.docker.internal:9101/mcp
```

或者使用宿主机的实际 IP 地址：
```
http://192.168.x.x:9101/mcp
```

### 方案 3: 选择正确的 Server Type

BrowserOS MCP Server 可能支持两种传输方式：

#### SSE (Server-Sent Events)
- **URL**: `http://host.docker.internal:9101/sse`
- **Server Type**: `sse`

#### Streamable HTTP
- **URL**: `http://host.docker.internal:9101/mcp`
- **Server Type**: `streamable-http`

**建议**: 先尝试 `streamable-http`，如果不行再试 `sse`

## 🧪 测试步骤

### 1. 手动测试连接

```bash
# 测试无认证
curl -X POST http://127.0.0.1:9101/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# 测试带 Bearer Token
curl -X POST http://127.0.0.1:9101/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

**成功的响应** 应该类似：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {...},
    "serverInfo": {...}
  }
}
```

**失败的响应** 可能是：
- `401 Unauthorized` → 需要认证
- `403 Forbidden` → 认证无效
- `Connection refused` → 服务未运行

### 2. 应用修复并重启

```bash
# 重启 RAGFlow 以应用改进的错误信息
./restart_ragflow_with_mcp_fix.sh
```

现在错误信息会更详细，告诉您具体是什么问题。

### 3. 在 RAGFlow 中测试

1. **打开 RAGFlow MCP 设置页面**
2. **点击 "Add MCP"**
3. **填写信息**:
   - Name: `BrowserOS`
   - URL: `http://host.docker.internal:9101/mcp`
   - Server Type: `streamable-http`
   - Headers: (如果需要认证)
     ```json
     {
       "Authorization": "Bearer YOUR_TOKEN"
     }
     ```
4. **点击测试按钮** (刷新图标)
5. **查看结果**:
   - ✅ 成功: 显示 "Connected · 29 tools available"
   - ❌ 失败: 查看详细错误信息

## 📊 常见错误及解决方案

### 错误 1: Connection refused

**原因**: BrowserOS MCP Server 未运行

**解决方案**:
1. 启动 BrowserOS 扩展
2. 确认 MCP Server 功能已启用
3. 检查端口 9101 是否被监听: `lsof -i :9101`

### 错误 2: 401 Unauthorized / 403 Forbidden

**原因**: 需要认证或认证无效

**解决方案**:
1. 在 BrowserOS 设置中查找 API Key/Token
2. 在 RAGFlow 的 Headers 中添加认证信息
3. 确认认证格式正确

### 错误 3: Timeout

**原因**: 网络连接问题或服务响应慢

**解决方案**:
1. 检查防火墙设置
2. 增加 timeout 值
3. 使用 `host.docker.internal` 而不是 `127.0.0.1`

### 错误 4: No tools available

**原因**: 连接成功但没有获取到工具

**解决方案**:
1. 检查 BrowserOS 配置
2. 确认 BrowserOS 已正确初始化
3. 查看 BrowserOS 日志

## 🔧 高级调试

### 查看详细日志

```bash
cd docker
docker compose logs -f ragflow-server | grep -i mcp
```

### 进入容器测试

```bash
cd docker
docker compose exec ragflow-server bash

# 在容器内测试
curl -X POST http://host.docker.internal:9101/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

### 检查网络连通性

```bash
# 从容器内 ping 宿主机
docker compose exec ragflow-server ping -c 3 host.docker.internal

# 检查端口是否可达
docker compose exec ragflow-server nc -zv host.docker.internal 9101
```

## 📝 配置示例

### 完整的 RAGFlow MCP 配置示例

```json
{
  "name": "BrowserOS",
  "url": "http://host.docker.internal:9101/mcp",
  "server_type": "streamable-http",
  "headers": {
    "Authorization": "Bearer your-browseros-token-here"
  },
  "timeout": 10
}
```

### BrowserOS 可能的认证格式

```json
// 格式 1: Bearer Token
{
  "Authorization": "Bearer sk-browseros-xxxxxxxxxxxxx"
}

// 格式 2: API Key
{
  "X-API-Key": "your-api-key"
}

// 格式 3: 自定义 Header
{
  "X-BrowserOS-Token": "your-token"
}
```

## 🎯 快速检查清单

- [ ] BrowserOS 扩展已安装并运行
- [ ] BrowserOS MCP Server 已启动
- [ ] 端口 9101 正在被监听
- [ ] 已获取 BrowserOS 的 API Key/Token
- [ ] URL 使用 `host.docker.internal` (Docker 环境)
- [ ] Server Type 选择正确 (`streamable-http` 或 `sse`)
- [ ] Headers 中包含正确的认证信息
- [ ] 已应用最新的错误处理修复
- [ ] 已重启 RAGFlow 服务

## 💡 提示

1. **优先检查认证**: 大多数 MCP Server 都需要某种形式的认证
2. **使用 host.docker.internal**: 在 Docker 环境中，这是访问宿主机服务的标准方式
3. **查看详细日志**: 应用修复后，错误信息会更详细
4. **测试两种传输方式**: 如果一种不行，尝试另一种

## 📞 需要帮助？

如果以上方法都不起作用：

1. 运行所有诊断脚本并保存输出
2. 检查 BrowserOS 官方文档
3. 查看 BrowserOS 的日志文件
4. 确认 BrowserOS 版本是否支持 MCP 协议

---

**最后更新**: 2025-10-30  
**适用版本**: RAGFlow 0.21 + BrowserOS MCP Server

