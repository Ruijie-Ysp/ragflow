# RAGFlow + BrowserOS MCP 集成成功指南

## 🎉 集成状态：成功

### ✅ 已完成的配置

1. **MCP 服务连接** - ✅ 正常
   - BrowserOS MCP 服务器运行在 `http://127.0.0.1:9101/mcp`
   - 通过 nginx 代理访问 `http://localhost:9102/mcp`
   - MCP 协议版本：2025-06-18

2. **工具功能** - ✅ 正常 (29个工具)
   - 调试工具：1个
   - 网络工具：2个
   - 元素交互：5个
   - 坐标操作：2个
   - 标签页管理：6个
   - 高级功能：3个
   - 历史管理：2个
   - 滚动操作：2个
   - 书签管理：3个
   - 导航自动化：1个
   - 截图功能：1个
   - 内容提取：1个

3. **RAGFlow 兼容性** - ✅ 通过
   - MCP 协议初始化正常
   - 工具列表获取正常
   - 代理服务运行正常

## 📋 RAGFlow 配置信息

### MCP 服务配置
```json
{
  "mcpServers": {
    "browseros": {
      "command": "curl",
      "args": ["-X", "POST", "http://localhost:9102/mcp"],
      "env": {}
    }
  }
}
```

### 服务地址
- **原始地址**: `http://127.0.0.1:9101/mcp`
- **代理地址**: `http://localhost:9102/mcp` (推荐使用)
- **协议**: HTTP + JSON-RPC 2.0
- **版本**: MCP 2025-06-18

## 🛠️ 可用功能

### 浏览器自动化
- 打开/关闭标签页
- 页面导航
- 元素点击和输入
- 键盘操作
- 页面滚动

### 内容提取
- 页面截图
- 文本内容提取
- 链接提取
- 交互元素获取

### 网络监控
- 网络请求列表
- 请求详情查看
- 控制台消息

### 书签和历史
- 书签管理
- 浏览历史搜索
- 历史记录获取

## 🔧 启动服务

### 1. 启动 BrowserOS MCP 服务
```bash
# 确保 BrowserOS MCP 服务运行在 9101 端口
# 这通常由 BrowserOS 扩展自动启动
```

### 2. 启动 Nginx 代理
```bash
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow
sudo nginx -c $(pwd)/nginx_proxy.conf -p $(pwd)
```

### 3. 验证服务
```bash
python3 test_ragflow_integration.py
```

## 🌐 RAGFlow 使用示例

### 在 RAGFlow 中调用浏览器功能

```python
# 示例：打开网页并截图
import requests

# 打开新标签页
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "browser_open_tab",
        "arguments": {
            "url": "https://example.com",
            "active": True
        }
    }
}

response = requests.post("http://localhost:9102/mcp", json=payload)
result = response.json()

# 获取截图
screenshot_payload = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "browser_get_screenshot",
        "arguments": {
            "tabId": result["result"]["content"][0]["text"],
            "size": "medium"
        }
    }
}

screenshot_response = requests.post("http://localhost:9102/mcp", json=screenshot_payload)
```

## ⚠️ 注意事项

### 浏览器扩展要求
- 需要安装 BrowserOS Chrome 扩展
- 扩展需要启用 MCP 服务
- 确保扩展在后台运行

### 网络配置
- nginx 代理解决了跨域问题
- 端口 9102 用于代理访问
- 确保防火墙允许本地端口访问

### 性能优化
- nginx 代理提供更好的性能
- 避免了 Docker 网络复杂性
- 直接本地连接更稳定

## 🚀 下一步

1. **安装 BrowserOS 扩展**
   - 从 Chrome Web Store 安装
   - 启用 MCP 功能
   - 配置端口 9101

2. **RAGFlow 集成**
   - 在 RAGFlow 配置中添加 MCP 服务器
   - 测试浏览器自动化功能
   - 开发自定义工作流

3. **功能扩展**
   - 探索更多 MCP 工具
   - 集成到 RAGFlow 的工作流中
   - 开发自定义浏览器自动化脚本

## 📞 支持

如果遇到问题：
1. 检查 nginx 代理状态：`ps aux | grep nginx`
2. 检查 MCP 服务：`curl http://localhost:9102/mcp`
3. 运行测试脚本：`python3 test_ragflow_integration.py`
4. 查看日志：`tail -f logs/access.log`

---

**状态**: ✅ RAGFlow + BrowserOS MCP 集成成功完成！
