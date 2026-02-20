# RAGFlow 代码备份 - 快速参考

## 🎯 一句话说明
**18 个文件已备份（15个修改 + 3个新增），支持一键对比、恢复和更新。**

---

## 📦 备份内容
- **API 层**: 3 个文件（Langfuse 集成、LLM 服务）
- **RAG 层**: 7 个文件（token 统计、prompts、flow）
- **Agent 层**: 5 个文件（agent_id 跟踪、工具）
- **Proxy 服务**: 3 个文件（OpenAI 代理服务器）**[新增]**

---

## ⚡ 常用命令

### 对比差异
```bash
cd docker/local_codes
./compare_with_current.sh           # 快速对比
./compare_with_current.sh --verbose # 详细对比
```

### 恢复代码
```bash
cd docker/local_codes
./restore_codes.sh                  # 一键恢复（会备份原文件）
```

### 更新备份
```bash
./backup_modified_codes.sh          # 在项目根目录运行
```

---

## 🔄 版本更新流程

```bash
# 1. 更新代码
git pull origin main

# 2. 对比差异
cd docker/local_codes && ./compare_with_current.sh

# 3. 恢复修改（如果无差异）
./restore_codes.sh

# 4. 手动合并（如果有差异）
vimdiff <backup_file> <current_file>

# 5. 重新构建
cd .. && docker build --build-arg LIGHTEN=1 -f Dockerfile -t infiniflow/ragflow:nightly-slim .

# 6. 测试
docker-compose up -d && docker-compose logs -f ragflow

# 7. 更新备份
cd .. && ./backup_modified_codes.sh
```

---

## 📚 文档

- **README.md** - 详细迁移指南
- **USAGE_GUIDE.md** - 使用指南和工作流
- **FILE_LIST.txt** - 文件清单
- **QUICK_REFERENCE.md** - 本文件

---

## 🔧 工具脚本

| 脚本 | 位置 | 功能 |
|------|------|------|
| `backup_modified_codes.sh` | 项目根目录 | 备份所有修改文件 |
| `compare_with_current.sh` | docker/local_codes/ | 对比差异 |
| `restore_codes.sh` | docker/local_codes/ | 恢复代码 |

---

## ⚠️ 注意事项

1. **定期备份** - 每次修改代码后运行备份脚本
2. **先对比再恢复** - 避免覆盖重要修改
3. **测试验证** - 恢复后务必测试功能
4. **保留备份** - 恢复脚本会自动备份原文件

---

## ✅ 快速检查

```bash
# 检查备份文件数量（应该是 15）
find docker/local_codes -name "*.py" | wc -l

# 验证备份完整性
cd docker/local_codes && ./compare_with_current.sh
```

---

**就这么简单！** 🚀

