# BrowserOS MCP 集成文档

本目录包含了 RAGFlow 与 BrowserOS MCP Server 集成的所有相关文件和脚本。

## 📁 文件说明

### 📋 配置文档
- **VSCode_CLINE_MCP_CONFIG.md** - VSCode Cline MCP 配置指南
- **BROWSEROS_MCP_SUCCESS_GUIDE.md** - BrowserOS MCP 成功配置指南
- **BROWSEROS_MCP_TROUBLESHOOTING.md** - 故障排除指南
- **RAGFLOW_BROWSEROS_SUCCESS.md** - RAGFlow 集成成功案例

### 🔧 安装和配置脚本
- **setup_browseros_proxy.sh** - 设置 BrowserOS MCP 代理（socat）
- **setup_nginx_proxy.sh** - 设置 BrowserOS MCP 代理（nginx）
- **start_browseros_for_vscode.sh** - 为 VSCode Cline 启动 BrowserOS 服务

### 🧪 测试脚本
- **test_browseros_connection.py** - BrowserOS MCP 连接测试
- **test_ragflow_integration.py** - RAGFlow 集成测试
- **test_browseros_mcp_auth.sh** - 认证测试脚本
- **diagnose_browseros_mcp.sh** - 诊断脚本

### ⚙️ 配置文件
- **nginx_proxy.conf** - Nginx 代理配置文件

## 🚀 快速开始

### 1. RAGFlow 集成
```bash
# 启动 nginx 代理
./setup_nginx_proxy.sh

# 测试集成
python3 test_ragflow_integration.py
```

### 2. VSCode Cline 集成
```bash
# 启动服务
./start_browseros_for_vscode.sh

# 按照 VSCode_CLINE_MCP_CONFIG.md 配置 Cline
```

### 3. 故障排除
```bash
# 运行诊断
./diagnose_browseros_mcp.sh

# 查看故障排除指南
cat BROWSEROS_MCP_TROUBLESHOOTING.md
```

## 📊 测试结果

✅ **已验证功能**：
- BrowserOS MCP Server 连接
- 29 个浏览器自动化工具
- RAGFlow 集成兼容性
- VSCode Cline 集成

⚠️ **注意事项**：
- BrowserOS MCP Server 只允许 localhost 访问
- 需要使用代理服务供 Docker 容器访问
- 确保端口 9101-9103 可用

## 🔗 相关链接

- BrowserOS MCP Server: `http://127.0.0.1:9101/mcp`
- RAGFlow 代理: `http://host.docker.internal:9102/mcp`
- VSCode Cline 代理: `http://localhost:9102/mcp`

## 📝 更新日志

- **2025-10-30**: 完成所有集成测试和文档整理
- **2025-10-30**: 创建统一的配置和测试脚本
- **2025-10-30**: 验证 RAGFlow 和 VSCode Cline 集成

---
*此目录由 RAGFlow 项目自动维护，包含所有 BrowserOS MCP 相关的配置和测试文件。*
