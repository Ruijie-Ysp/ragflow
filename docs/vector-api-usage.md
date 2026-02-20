# 向量数据 API 使用文档

## 概述

RAGFlow 现在支持在 chunk 列表 API 中返回向量元数据，用于前端展示和分析。

## API 端点

### 1. Chunk 列表 API（内部使用）

**端点**: `POST /api/chunk/list`

**请求参数**:
```json
{
  "doc_id": "文档ID",
  "page": 1,
  "size": 30,
  "keywords": "搜索关键词（可选）",
  "available_int": 1,
  "include_vector": true,           // 是否包含向量元数据
  "include_full_vector": false      // 是否包含完整向量数据（可选）
}
```

**响应示例**（include_vector=true, include_full_vector=false）:
```json
{
  "code": 0,
  "data": {
    "total": 100,
    "chunks": [
      {
        "chunk_id": "abc123",
        "content_with_weight": "这是文本内容...",
        "doc_id": "doc123",
        "docnm_kwd": "文档名称",
        "important_kwd": ["关键词1", "关键词2"],
        "question_kwd": [],
        "image_id": "",
        "available_int": 1,
        "positions": [[0, 0, 100, 100, 1]],
        "vector_metadata": {
          "dimension": 1024,
          "field_name": "q_1024_vec",
          "mean": 0.0123,
          "std": 0.4567,
          "min": -2.3456,
          "max": 3.4567,
          "norm": 12.3456
        }
      }
    ],
    "doc": {
      "id": "doc123",
      "name": "文档名称"
    }
  }
}
```

**响应示例**（include_vector=true, include_full_vector=true）:
```json
{
  "code": 0,
  "data": {
    "chunks": [
      {
        "chunk_id": "abc123",
        "content_with_weight": "这是文本内容...",
        "vector_metadata": {
          "dimension": 1024,
          "field_name": "q_1024_vec",
          "mean": 0.0123,
          "std": 0.4567,
          "min": -2.3456,
          "max": 3.4567,
          "norm": 12.3456,
          "vector": [0.123, -0.456, 0.789, ...]  // 完整的1024维向量
        }
      }
    ]
  }
}
```

### 2. Chunk 列表 API（外部 API）

**端点**: `POST /api/list_chunks`

**请求参数**:
```json
{
  "doc_id": "文档ID",
  "include_vector": true,           // 是否包含向量元数据
  "include_full_vector": false      // 是否包含完整向量数据（可选）
}
```

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {
      "content": "这是文本内容...",
      "doc_name": "文档名称",
      "image_id": "",
      "chunk_id": "abc123",
      "vector_metadata": {
        "dimension": 1024,
        "field_name": "q_1024_vec",
        "mean": 0.0123,
        "std": 0.4567,
        "min": -2.3456,
        "max": 3.4567,
        "norm": 12.3456
      }
    }
  ]
}
```

## 向量元数据字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| dimension | int | 向量维度（通常为1024） |
| field_name | string | 向量字段名称（格式：q_{dim}_vec） |
| mean | float | 向量所有元素的均值 |
| std | float | 向量所有元素的标准差 |
| min | float | 向量中的最小值 |
| max | float | 向量中的最大值 |
| norm | float | 向量的L2范数（欧几里得范数） |
| vector | float[] | 完整向量数据（仅当 include_full_vector=true 时返回） |

## 使用建议

1. **性能考虑**：
   - 默认不返回向量数据（include_vector=false）
   - 仅在需要时启用向量元数据（include_vector=true）
   - 避免频繁请求完整向量（include_full_vector=true），因为数据量大

2. **分页**：
   - 建议使用分页加载，每页不超过50条
   - 启用完整向量时，建议每页不超过20条

3. **缓存**：
   - 向量元数据相对稳定，可以在前端缓存
   - 完整向量数据较大，下载后建议保存到本地

## 前端集成示例

参见以下文件：
- `web/src/hooks/use-vector-metadata.ts` - 向量数据获取 Hook
- `web/src/components/vector-metadata-panel.tsx` - 向量元数据展示面板
- `web/src/components/vector-statistics-summary.tsx` - 向量统计汇总
- `web/src/pages/chunk/vector-tab.tsx` - 向量数据标签页示例

