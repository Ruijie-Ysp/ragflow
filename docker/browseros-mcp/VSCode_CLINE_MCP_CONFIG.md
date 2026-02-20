# VSCode Cline MCP 配置指南 - BrowserOS

## 📋 配置文件位置

配置文件位于：
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

## 🔧 BrowserOS MCP 配置

### 当前配置
```json
{
  "mcpServers": {
    "browseros": {
      "autoApprove": [
        "list_console_messages",
        "list_network_requests",
        "get_network_request",
        "browser_type_text",
        "browser_type_at_coordinates",
        "browser_switch_tab",
        "browser_send_keys",
        "browser_search_history",
        "browser_scroll_up",
        "browser_scroll_to_element",
        "browser_scroll_down",
        "browser_remove_bookmark",
        "browser_open_tab",
        "browser_navigate",
        "browser_list_tabs",
        "browser_get_screenshot",
        "browser_get_recent_history",
        "browser_get_page_content",
        "browser_get_load_status",
        "browser_get_interactive_elements",
        "browser_get_bookmarks",
        "browser_get_active_tab",
        "browser_execute_javascript",
        "browser_create_bookmark",
        "browser_close_tab",
        "browser_click_element",
        "browser_click_coordinates",
        "browser_clear_input",
        "browser_check_availability"
      ],
      "disabled": false,
      "timeout": 120,
      "type": "sse",
      "url": "http://localhost:9102/mcp",
      "description": "BrowserOS MCP server for browser automation and web interaction"
    }
  }
}
```

## 🚀 启动步骤

### 1. 确保 BrowserOS MCP 服务运行
```bash
# 检查服务状态
curl http://localhost:9102/mcp

# 如果服务未运行，启动 nginx 代理
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow
sudo nginx -c $(pwd)/nginx_proxy.conf -p $(pwd)
```

### 2. 重启 VSCode 或重新加载 Cline
- 按 `Cmd+Shift+P` 打开命令面板
- 输入 `Developer: Reload Window` 重启 VSCode
- 或者重启 VSCode 应用

### 3. 验证配置
在 Cline 中，你应该能看到 BrowserOS 工具可用，包括：
- 浏览器标签页管理
- 页面导航和交互
- 截图和内容提取
- 网络请求监控

## 🛠️ 可用工具列表

### 标签页管理
- `browser_list_tabs` - 列出所有标签页
- `browser_open_tab` - 打开新标签页
- `browser_close_tab` - 关闭标签页
- `browser_switch_tab` - 切换标签页
- `browser_get_active_tab` - 获取当前活动标签页

### 页面导航
- `browser_navigate` - 导航到指定URL
- `browser_get_load_status` - 检查页面加载状态

### 元素交互
- `browser_click_element` - 点击元素
- `browser_click_coordinates` - 点击坐标
- `browser_type_text` - 输入文本
- `browser_clear_input` - 清空输入框
- `browser_send_keys` - 发送键盘按键

### 页面操作
- `browser_scroll_up` - 向上滚动
- `browser_scroll_down` - 向下滚动
- `browser_scroll_to_element` - 滚动到元素

### 内容提取
- `browser_get_screenshot` - 截图
- `browser_get_page_content` - 获取页面内容
- `browser_get_interactive_elements` - 获取交互元素

### 高级功能
- `browser_execute_javascript` - 执行JavaScript
- `browser_type_at_coordinates` - 在坐标处输入

### 网络监控
- `list_network_requests` - 列出网络请求
- `get_network_request` - 获取网络请求详情
- `list_console_messages` - 列出控制台消息

### 书签和历史
- `browser_get_bookmarks` - 获取书签
- `browser_create_bookmark` - 创建书签
- `browser_remove_bookmark` - 删除书签
- `browser_search_history` - 搜索历史
- `browser_get_recent_history` - 获取最近历史

### 系统检查
- `browser_check_availability` - 检查可用性

## ⚙️ 配置参数说明

- **autoApprove**: 自动批准的工具列表，无需手动确认
- **disabled**: 是否禁用服务 (false=启用)
- **timeout**: 超时时间 (秒)
- **type**: 连接类型 ("sse" 表示 Server-Sent Events)
- **url**: MCP 服务地址
- **description**: 服务描述

## 🔍 故障排除

### 1. 工具不可用
```bash
# 检查 nginx 代理状态
ps aux | grep nginx

# 检查端口占用
lsof -i :9102

# 测试 MCP 连接
curl -X POST http://localhost:9102/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

### 2. 重启服务
```bash
# 停止 nginx
sudo nginx -s quit

# 重新启动
cd /Users/yangshengpeng/Desktop/openAI/ragflow-0.21/ragflow
sudo nginx -c $(pwd)/nginx_proxy.conf -p $(pwd)
```

### 3. 检查日志
```bash
# 查看 nginx 访问日志
tail -f logs/access.log

# 查看错误日志
tail -f logs/error.log
```

## 📝 使用示例

### 在 Cline 中使用 BrowserOS

1. **打开网页并截图**
```
请帮我打开 https://example.com 并截取页面截图
```

2. **提取页面内容**
```
请提取当前页面的所有文本内容
```

3. **页面交互**
```
请点击页面上的"登录"按钮，然后输入用户名"test"
```

4. **网络监控**
```
请列出当前页面的所有网络请求
```

## 🎯 最佳实践

1. **确保服务稳定**: 使用 nginx 代理而不是直接连接
2. **合理设置超时**: 120秒超时适合大多数浏览器操作
3. **自动批准常用工具**: 避免频繁手动确认
4. **定期检查服务状态**: 确保代理服务正常运行

---

**配置完成！** 现在你可以在 VSCode 的 Cline 中使用 BrowserOS MCP 服务进行浏览器自动化操作了。
