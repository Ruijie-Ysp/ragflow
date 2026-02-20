# RAGFlow + BrowserOS MCP 快速开始指南

## 🎯 目标

成功将 BrowserOS MCP Server 连接到 RAGFlow，获取 29 个浏览器自动化工具。

## 📋 前提条件

- ✅ RAGFlow 已安装并运行（Docker 环境）
- ✅ BrowserOS 扩展已安装
- ⚠️ BrowserOS MCP Server 需要认证（这是关键！）

## 🚀 快速开始（3 步）

### 步骤 1: 获取 BrowserOS 认证信息

1. **打开 BrowserOS 扩展设置**
2. **查找 MCP Server 配置**
3. **记录以下信息**:
   - API Key / Token
   - Server Port (通常是 9101)
   - Server Type (sse 或 streamable-http)

### 步骤 2: 应用 RAGFlow 修复

```bash
# 进入 RAGFlow 目录
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow

# 运行重启脚本（会自动挂载修复的文件）
./restart_ragflow_with_mcp_fix.sh
```

### 步骤 3: 在 RAGFlow 中添加 MCP 服务器

1. **打开 RAGFlow Web 界面**
2. **进入 Profile Settings → MCP Servers**
3. **点击 "Add MCP"**
4. **填写配置**:

   ```
   Name: BrowserOS
   URL: http://host.docker.internal:9101/mcp
   Server Type: streamable-http
   ```

5. **重要！添加 Headers**:
   
   点击 Headers 展开，添加认证信息：
   
   ```json
   {
     "Authorization": "Bearer YOUR_BROWSEROS_TOKEN_HERE"
   }
   ```
   
   **替换 `YOUR_BROWSEROS_TOKEN_HERE` 为您从 BrowserOS 获取的实际 Token！**

6. **点击测试按钮**（刷新图标）

7. **预期结果**: 
   - ✅ 成功: "Connected · 29 tools available"
   - ❌ 失败: 查看详细错误信息

## 🔍 如果连接失败

### 检查 1: BrowserOS 是否运行

```bash
# 检查端口 9101 是否被监听
lsof -i :9101

# 或者运行诊断脚本
./diagnose_browseros_mcp.sh
```

### 检查 2: 认证信息是否正确

```bash
# 运行认证测试脚本
./test_browseros_mcp_auth.sh
```

### 检查 3: 查看详细错误

现在错误信息会更详细，告诉您具体问题：

- **Connection refused** → BrowserOS 未运行
- **401/403** → 认证信息错误
- **Timeout** → 网络问题

```bash
# 查看 RAGFlow 日志
cd docker
docker compose logs -f ragflow-server | grep -i mcp
```

## 📝 常见配置

### 配置 1: 使用 Bearer Token（推荐）

```json
{
  "name": "BrowserOS",
  "url": "http://host.docker.internal:9101/mcp",
  "server_type": "streamable-http",
  "headers": {
    "Authorization": "Bearer sk-browseros-xxxxx"
  }
}
```

### 配置 2: 使用 API Key

```json
{
  "name": "BrowserOS",
  "url": "http://host.docker.internal:9101/mcp",
  "server_type": "streamable-http",
  "headers": {
    "X-API-Key": "your-api-key"
  }
}
```

### 配置 3: 使用 SSE 传输

```json
{
  "name": "BrowserOS",
  "url": "http://host.docker.internal:9101/sse",
  "server_type": "sse",
  "headers": {
    "Authorization": "Bearer your-token"
  }
}
```

## 🛠️ 可用的脚本

| 脚本 | 用途 |
|------|------|
| `restart_ragflow_with_mcp_fix.sh` | 重启 RAGFlow 并应用修复 |
| `verify_mcp_fix.sh` | 验证修复是否正确应用 |
| `diagnose_browseros_mcp.sh` | 诊断 BrowserOS 连接问题 |
| `test_browseros_mcp_auth.sh` | 测试不同的认证方式 |

## 📚 详细文档

- **MCP_BUG_FIX_README.md** - 修复详情和技术说明
- **BROWSEROS_MCP_TROUBLESHOOTING.md** - 完整的故障排除指南

## ✅ 成功标志

当您看到以下内容时，说明配置成功：

```
✅ Connected · 29 tools available
```

可用的工具包括：
- list_console_messages
- list_network_requests
- browser_type_text
- browser_click_element
- browser_navigate
- ... 等 29 个工具

## 🎉 下一步

成功连接后，您可以：

1. **在 Agent 中使用 BrowserOS 工具**
2. **创建浏览器自动化工作流**
3. **测试不同的浏览器操作**

## ⚠️ 重要提示

1. **必须使用 `host.docker.internal`** 而不是 `127.0.0.1`（Docker 环境）
2. **必须提供正确的认证信息**（这是最常见的问题）
3. **确保 BrowserOS MCP Server 正在运行**
4. **选择正确的 Server Type**（streamable-http 或 sse）

## 🐛 仍然有问题？

1. 查看 **BROWSEROS_MCP_TROUBLESHOOTING.md** 获取详细的故障排除步骤
2. 运行所有诊断脚本
3. 检查 RAGFlow 和 BrowserOS 的日志
4. 确认 BrowserOS 版本支持 MCP 协议

---

**祝您使用愉快！** 🚀

