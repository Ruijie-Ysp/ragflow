# RAGFlow OpenAI 代理调试工具集

## 概述

本工具集用于诊断和解决 RAGFlow OpenAI 代理返回内容不显示的问题。

## 问题背景

**现象**：
- ✅ 调用标准 OpenAI 接口（`http://10.0.154.103:8080/v1`）能正常会话
- ❌ 调用 RAGFlow 代理接口（`http://localhost:10101/v1`）返回内容不显示

**目标**：
- 分析 RAGFlow 代理的返回格式是否符合标准 OpenAI 格式
- 找出导致内容不显示的根本原因
- 提供修复方案

## 文件说明

### 1. `ragflow_openai_proxy.py` (已增强)

**改进内容**：
- ✅ 增加详细的请求和响应日志
- ✅ 解析并验证 RAGFlow 返回的 JSON 结构
- ✅ 检查 `content` 字段是否为空
- ✅ 增强响应头设置（添加 `charset=utf-8`）
- ✅ 改进错误处理和堆栈跟踪

**日志输出示例**：
```
📨 收到请求: agent_id=xxx, stream=False
📥 RAGFlow 响应状态码: 200
📥 RAGFlow 响应头: {...}
✅ RAGFlow 响应数据结构:
{
  "id": "...",
  "choices": [
    {
      "message": {
        "content": "你好！我是..."
      }
    }
  ]
}
✅ 提取的内容长度: 52 字符
✅ 内容预览: 你好！我是...
```

### 2. `quick_diagnosis.py` (新增)

**功能**：快速诊断所有服务的状态

**用法**：
```bash
# 自动检测所有服务
python quick_diagnosis.py

# 指定 Agent ID 进行测试
python quick_diagnosis.py <agent_id>
```

**检查项目**：
- ✅ 标准 OpenAI API 是否可访问
- ✅ RAGFlow API 是否可访问
- ✅ 代理服务是否运行
- ✅ 列出所有可用的 Agent
- ✅ 执行简单的请求测试

### 3. `test_ragflow_direct.py` (新增)

**功能**：直接测试 RAGFlow Agent API

**用法**：
```bash
# 列出所有 Agent
python test_ragflow_direct.py

# 测试指定 Agent
python test_ragflow_direct.py <agent_id>
```

**测试内容**：
- ✅ 非流式响应的完整结构
- ✅ 流式响应的逐行输出
- ✅ 提取并显示实际内容
- ✅ 验证响应格式

### 4. `test_all_apis.py` (新增)

**功能**：综合对比三个 API 的返回

**用法**：
```bash
# 对比所有 API
python test_all_apis.py <agent_id>
```

**对比内容**：
- ✅ 标准 OpenAI API（非流式 + 流式）
- ✅ RAGFlow 原始 API（非流式 + 流式）
- ✅ 代理 API（非流式 + 流式）
- ✅ 生成对比表格
- ✅ 检查内容一致性

### 5. `PROXY_ANALYSIS.md` (新增)

**内容**：
- 详细的问题分析
- RAGFlow API 返回格式说明
- 代理代码的工作原理
- 可能的问题点和修复方案

### 6. `TESTING_GUIDE.md` (新增)

**内容**：
- 完整的测试步骤
- 问题诊断指南
- 常见问题解答
- 代码改进说明

## 快速开始

### 步骤 1: 运行快速诊断

```bash
cd docker/local_codes
python quick_diagnosis.py
```

这会检查所有服务的状态，并列出可用的 Agent。

### 步骤 2: 测试 RAGFlow 原始 API

使用诊断工具显示的 Agent ID：

```bash
python test_ragflow_direct.py <agent_id>
```

**预期结果**：
- 应该看到完整的 JSON 响应
- `choices[0].message.content` 应该包含实际内容

**如果失败**：
- 检查 Agent 是否正确配置了 LLM
- 检查 RAGFlow 服务日志

### 步骤 3: 启动增强版代理

```bash
python ragflow_openai_proxy.py
```

### 步骤 4: 综合测试

```bash
python test_all_apis.py <agent_id>
```

查看对比结果，确认代理是否正常工作。

## 问题诊断流程

```
开始
  ↓
运行 quick_diagnosis.py
  ↓
所有服务正常？
  ├─ 否 → 修复服务问题
  └─ 是 ↓
运行 test_ragflow_direct.py
  ↓
RAGFlow 返回内容？
  ├─ 否 → 检查 Agent 配置
  └─ 是 ↓
启动代理服务
  ↓
运行 test_all_apis.py
  ↓
代理返回内容？
  ├─ 否 → 查看代理日志，检查转发逻辑
  └─ 是 ↓
问题解决！
```

## 常见问题排查

### 问题 1: RAGFlow 返回内容为空

**检查**：
1. Agent 是否配置了 LLM？
2. LLM 服务是否正常？
3. 查看 RAGFlow 日志

**解决**：
- 在 RAGFlow UI 中检查 Agent 配置
- 测试 LLM 服务是否可用
- 重启 RAGFlow 服务

### 问题 2: 代理转发失败

**检查**：
1. 代理服务日志中的错误信息
2. RAGFlow 返回的状态码
3. 响应头是否正确

**解决**：
- 查看 `ragflow_openai_proxy.py` 的日志输出
- 确认 RAGFlow API Key 正确
- 检查网络连接

### 问题 3: 客户端不显示内容

**检查**：
1. 使用 `curl` 测试代理 API
2. 检查客户端的错误日志
3. 对比标准 OpenAI API 的响应

**解决**：
- 确认响应格式符合 OpenAI 标准
- 检查客户端的 JSON 解析逻辑
- 查看客户端的网络请求详情

## 响应格式对比

### 标准 OpenAI API

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen3-32b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### RAGFlow API (通过代理)

```json
{
  "id": "session-id",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "agent-id",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "你好！我是..."
      },
      "logprobs": null,
      "finish_reason": "stop",
      "index": 0
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30,
    "completion_tokens_details": {
      "reasoning_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    }
  }
}
```

**差异**：
- ✅ 核心结构完全兼容
- ⚠️ RAGFlow 多了 `completion_tokens_details` 字段
- ⚠️ 字段顺序略有不同
- ✅ `choices[0].message.content` 字段一致

## 环境变量

```bash
# RAGFlow 配置
export RAGFLOW_BASE_URL="http://localhost:80"
export RAGFLOW_API_KEY="ragflow-xxx"

# 运行代理
python ragflow_openai_proxy.py
```

## 测试用例

### 使用 curl 测试

**非流式**：
```bash
curl -X POST http://localhost:10101/v1/chat/completions \
  -H "Authorization: Bearer <agent_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "any",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

**流式**：
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

### 使用 Python OpenAI 客户端

```python
from openai import OpenAI

client = OpenAI(
    api_key="<agent_id>",
    base_url="http://localhost:10101/v1"
)

response = client.chat.completions.create(
    model="any",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

## 下一步

如果问题仍未解决：

1. **收集完整日志**：
   - 运行 `quick_diagnosis.py` 并保存输出
   - 运行 `test_all_apis.py` 并保存输出
   - 保存代理服务器的日志

2. **提供详细信息**：
   - RAGFlow 版本
   - Agent 配置
   - 客户端代码和错误信息

3. **检查 RAGFlow 源码**：
   - 查看 `api/apps/sdk/session.py` 中的 `agents_completion_openai_compatibility` 函数
   - 查看 `api/db/services/canvas_service.py` 中的 `completionOpenAI` 函数

## 总结

本工具集提供了完整的诊断和测试流程，帮助你：
- ✅ 快速定位问题
- ✅ 对比不同 API 的返回
- ✅ 验证代理的正确性
- ✅ 收集详细的调试信息

通过这些工具，你应该能够找出代理返回内容不显示的根本原因。

