# RAGFlow OpenAI 代理测试指南

## 问题描述

调用标准 OpenAI 接口能正常会话，但通过 `ragflow_openai_proxy.py` 提供的代理接口调用时，返回内容不显示。

## 测试步骤

### 步骤 1: 准备环境

确保以下服务正在运行：
- ✅ 标准 OpenAI 兼容服务（`http://10.0.154.103:8080/v1`）
- ✅ RAGFlow 服务（默认 `http://localhost:80`）
- ✅ RAGFlow OpenAI 代理服务（`http://localhost:10101`）

### 步骤 2: 启动代理服务器（增强版）

代理服务器已经更新，包含详细的调试日志：

```bash
cd docker/local_codes
python ragflow_openai_proxy.py
```

你应该看到类似的输出：
```
🚀 RAGFlow OpenAI 代理服务器启动中...
📍 RAGFlow 地址: http://localhost:80
🔑 RAGFlow API Key: ragflow-RkZTliMTlhYT...
🌐 代理服务器地址: http://localhost:10101
📝 使用方法: 将 agent_id 作为 API key
```

### 步骤 3: 获取 Agent ID

首先需要获取你的 Agent ID。运行以下脚本：

```bash
python test_ragflow_direct.py
```

这会列出所有可用的 Agent，选择一个 Agent ID 用于后续测试。

### 步骤 4: 测试 RAGFlow 原始 API

使用获取到的 Agent ID 测试 RAGFlow 的原始 API：

```bash
python test_ragflow_direct.py <your_agent_id>
```

**预期输出**：
- ✅ 非流式响应应该包含完整的 JSON 结构
- ✅ `choices[0].message.content` 应该包含实际内容
- ✅ 流式响应应该逐行输出内容

**如果失败**：
- 检查 Agent ID 是否正确
- 检查 RAGFlow API Key 是否有效
- 检查 RAGFlow 服务是否正常运行

### 步骤 5: 综合对比测试

运行综合测试脚本，对比三个 API 的返回：

```bash
python test_all_apis.py <your_agent_id>
```

这个脚本会：
1. 测试标准 OpenAI API（非流式和流式）
2. 测试 RAGFlow 原始 API（非流式和流式）
3. 测试代理 API（非流式和流式）
4. 对比所有结果

**预期输出**：
```
================================================================================
  测试结果对比
================================================================================

API                       状态       状态码     耗时(秒)     内容长度     内容预览
------------------------------------------------------------------------------------------------------------------------
标准 OpenAI (非流式)      ✅ 成功    200        1.23         45           你好！我是一个AI助手...
RAGFlow 原始 (非流式)     ✅ 成功    200        2.34         52           你好！我是RAGFlow...
代理 API (非流式)         ✅ 成功    200        2.35         52           你好！我是RAGFlow...
```

### 步骤 6: 查看代理服务器日志

在代理服务器的终端中，你应该看到详细的日志输出：

**非流式请求的日志示例**：
```
📨 收到请求: agent_id=xxx, stream=False
📥 RAGFlow 响应状态码: 200
📥 RAGFlow 响应头: {'Content-Type': 'application/json', ...}
✅ RAGFlow 响应数据结构:
{
  "id": "session-id",
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "你好！我是..."
      },
      "finish_reason": "stop",
      "index": 0
    }
  ],
  ...
}
✅ 提取的内容长度: 52 字符
✅ 内容预览: 你好！我是...
```

**流式请求的日志示例**：
```
📨 收到请求: agent_id=xxx, stream=True
📨 流式响应 #1: data: {"id":"xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"你"},...
📨 流式响应 #2: data: {"id":"xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"好"},...
...
✅ 流式响应完成，共 50 行
```

## 问题诊断

### 问题 1: 代理返回 401 错误

**症状**：
```json
{
  "error": {
    "message": "Missing or invalid Authorization header. Use agent_id as API key.",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

**解决方案**：
- 确保在请求头中包含 `Authorization: Bearer <agent_id>`
- 检查 Agent ID 是否正确

### 问题 2: 代理返回 500 错误

**症状**：
```json
{
  "error": {
    "message": "Failed to connect to RAGFlow",
    "type": "server_error"
  }
}
```

**解决方案**：
- 检查 RAGFlow 服务是否运行
- 检查 `RAGFLOW_BASE_URL` 环境变量是否正确
- 检查网络连接

### 问题 3: 返回内容为空

**症状**：
- 状态码 200
- 响应结构正确
- 但 `choices[0].message.content` 为空字符串

**可能原因**：
1. RAGFlow Agent 没有配置 LLM
2. RAGFlow Agent 的提示词有问题
3. RAGFlow 后端服务异常

**诊断步骤**：
1. 查看代理服务器日志，确认 RAGFlow 返回的内容
2. 直接测试 RAGFlow 原始 API（使用 `test_ragflow_direct.py`）
3. 检查 RAGFlow 的日志

### 问题 4: 流式响应不显示

**症状**：
- 非流式响应正常
- 流式响应没有内容或卡住

**可能原因**：
1. 客户端不支持 SSE（Server-Sent Events）
2. 代理服务器的响应头设置不正确
3. 网络中间件缓冲了流式响应

**解决方案**：
- 检查代理服务器日志，确认流式数据是否正常发送
- 使用 `curl` 测试流式响应：
  ```bash
  curl -N -X POST http://localhost:10101/v1/chat/completions \
    -H "Authorization: Bearer <agent_id>" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "any",
      "messages": [{"role": "user", "content": "你好"}],
      "stream": true
    }'
  ```

## 代码改进说明

### 增强的日志输出

代理服务器现在会输出：
1. **请求信息**：agent_id、stream 参数
2. **RAGFlow 响应状态**：状态码、响应头
3. **响应内容解析**：JSON 结构、content 字段
4. **流式响应**：每一行的内容（前 100 字符）

### 增强的响应头

非流式响应现在包含：
- `Content-Type: application/json; charset=utf-8`
- `Cache-Control: no-cache`

流式响应现在包含：
- `Content-Type: text/event-stream; charset=utf-8`
- `Cache-Control: no-cache`
- `X-Accel-Buffering: no`
- `Connection: keep-alive`

### 错误处理

代理现在会：
1. 检查 RAGFlow 的响应状态码
2. 解析并验证响应 JSON
3. 检查 content 字段是否为空
4. 打印详细的错误堆栈

## 下一步

如果问题仍然存在：

1. **收集日志**：
   - 代理服务器的完整日志
   - RAGFlow 服务器的日志
   - 客户端的错误信息

2. **提供测试结果**：
   - `test_ragflow_direct.py` 的输出
   - `test_all_apis.py` 的输出
   - 实际使用的客户端代码

3. **检查 RAGFlow 配置**：
   - Agent 是否正确配置了 LLM
   - LLM 服务是否正常
   - API Key 是否有效

## 常见问题

### Q: 为什么标准 OpenAI API 能用，但代理不能用？

A: 可能的原因：
1. 代理转发的请求格式不正确
2. RAGFlow 返回的响应格式与标准 OpenAI 不完全一致
3. 客户端对响应格式有特殊要求

### Q: 如何确认代理是否正常工作？

A: 运行 `test_all_apis.py`，对比三个 API 的返回。如果 RAGFlow 原始 API 和代理 API 的返回一致，说明代理工作正常。

### Q: 如何调试客户端问题？

A: 
1. 使用 `curl` 或 `httpie` 等工具直接测试 API
2. 查看客户端的网络请求和响应
3. 检查客户端是否正确解析 JSON 响应

## 联系支持

如果以上步骤都无法解决问题，请提供：
1. 完整的测试日志
2. RAGFlow 版本信息
3. 客户端代码和错误信息

