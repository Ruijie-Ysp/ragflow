# 知识图谱性能瓶颈分析报告

## 问题描述
在智能体(Agent)中引用知识库并开启知识图谱功能后,系统响应速度显著变慢。

## 性能瓶颈定位

### 🔴 严重问题 1: 重复调用知识图谱检索

**位置**: `agent/tools/retrieval.py` 和 `docker/local_codes/agent/tools/retrieval.py`

**问题代码**:
```python
# 第162-169行: 第一次调用
if self._param.use_kg:
    ck = settings.kg_retriever.retrieval(query,
                                           [kb.tenant_id for kb in kbs],
                                           kb_ids,
                                           embd_mdl,
                                           LLMBundle(self._canvas.get_tenant_id(), LLMType.CHAT, agent_id=self._canvas.get_agent_id()))
    if ck["content_with_weight"]:
        kbinfos["chunks"].insert(0, ck)

# 第173-178行: 第二次调用 (重复!)
if self._param.use_kg and kbs:
    ck = settings.kg_retriever.retrieval(query, [kb.tenant_id for kb in kbs], filtered_kb_ids, embd_mdl, LLMBundle(kbs[0].tenant_id, LLMType.CHAT, agent_id=self._canvas.get_agent_id()))
    if ck["content_with_weight"]:
        ck["content"] = ck["content_with_weight"]
        del ck["content_with_weight"]
        kbinfos["chunks"].insert(0, ck)
```

**影响**: 
- 每次查询都会执行**两次完整的知识图谱检索**
- 性能损失翻倍,包括LLM调用、向量检索、ES查询等所有开销

---

### 🔴 严重问题 2: LLM查询重写开销大

**位置**: `graphrag/search.py` 第44-65行

**问题代码**:
```python
def query_rewrite(self, llm, question, idxnms, kb_ids):
    # 1. 同步调用trio.run获取实体类型样本 (阻塞)
    ty2ents = trio.run(lambda: get_entity_type2samples(idxnms, kb_ids))
    
    # 2. 构建提示词,可能包含大量实体类型数据
    hint_prompt = PROMPTS["minirag_query2kwd"].format(query=question,
                                                      TYPE_POOL=json.dumps(ty2ents, ensure_ascii=False, indent=2))
    
    # 3. 调用LLM进行查询改写 (耗时)
    result = self._chat(llm, hint_prompt, [{"role": "user", "content": "Output:"}], {})
```

**性能问题**:
1. **同步阻塞**: `trio.run()` 在主线程中同步执行异步操作
2. **ES查询开销**: `get_entity_type2samples()` 查询size=10000的实体类型数据
3. **LLM调用延迟**: 每次都需要调用LLM进行查询改写,即使有缓存也需要检查

**代码位置**: `graphrag/utils.py` 第557-572行
```python
async def get_entity_type2samples(idxnms, kb_ids: list):
    # 查询10000条实体类型数据!
    es_res = await trio.to_thread.run_sync(lambda: settings.retriever.search({
        "knowledge_graph_kwd": "ty2ents", 
        "kb_id": kb_ids, 
        "size": 10000,  # ⚠️ 大量数据
        "fields": ["content_with_weight"]
    }, idxnms, kb_ids))
```

---

### 🟡 中等问题 3: 多次向量化计算

**位置**: `graphrag/search.py` 第167-169行

**问题代码**:
```python
# retrieval方法中的多次向量化
ents_from_query = self.get_relevant_ents_by_keywords(ents, filters, idxnms, kb_ids, emb_mdl, ent_sim_threshold)  # 向量化1
ents_from_types = self.get_relevant_ents_by_types(ty_kwds, filters, idxnms, kb_ids, 10000)
rels_from_txt = self.get_relevant_relations_by_txt(qst, filters, idxnms, kb_ids, emb_mdl, rel_sim_threshold)  # 向量化2
```

**详细分析**:

1. **实体关键词向量化** (第106-115行):
```python
def get_relevant_ents_by_keywords(self, keywords, filters, idxnms, kb_ids, emb_mdl, sim_thr=0.3, N=56):
    filters["knowledge_graph_kwd"] = "entity"
    matchDense = self.get_vector(", ".join(keywords), emb_mdl, 1024, sim_thr)  # 向量化
    es_res = self.dataStore.search([...], filters, [matchDense], ...)
```

2. **关系文本向量化** (第117-126行):
```python
def get_relevant_relations_by_txt(self, txt, filters, idxnms, kb_ids, emb_mdl, sim_thr=0.3, N=56):
    filters["knowledge_graph_kwd"] = "relation"
    matchDense = self.get_vector(txt, emb_mdl, 1024, sim_thr)  # 向量化
    es_res = self.dataStore.search([...], filters, [matchDense], ...)
```

**影响**: 每次检索需要2-3次embedding模型调用

---

### 🟡 中等问题 4: 按类型检索实体数量过大

**位置**: `graphrag/search.py` 第168行

**问题代码**:
```python
# 检索10000个实体!
ents_from_types = self.get_relevant_ents_by_types(ty_kwds, filters, idxnms, kb_ids, 10000)
```

**实现代码** (第128-138行):
```python
def get_relevant_ents_by_types(self, types, filters, idxnms, kb_ids, N=56):
    if not types:
        return {}
    filters = deepcopy(filters)
    filters["knowledge_graph_kwd"] = "entity"
    filters["entity_type_kwd"] = types
    ordr = OrderByExpr()
    ordr.desc("rank_flt")
    # N=10000 导致ES查询大量数据
    es_res = self.dataStore.search(["entity_kwd", "rank_flt"], [], filters, [], ordr, 0, N, idxnms, kb_ids)
    return self._ent_info_from_(es_res, 0)
```

**影响**: 
- ES需要检索和排序10000条记录
- 内存占用大
- 网络传输开销大

---

### 🟡 中等问题 5: 关系描述的额外查询

**位置**: `graphrag/search.py` 第240-248行

**问题代码**:
```python
for (f, t), rel in rels_from_txt:
    if not rel.get("description"):
        # 对每个缺少描述的关系,循环查询所有tenant
        for tid in tenant_ids:
            rela = get_relation(tid, kb_ids, f, t)  # 额外的ES查询
            if rela:
                break
        else:
            continue
        rel["description"] = rela["description"]
```

**get_relation实现** (`graphrag/utils.py` 第326-345行):
```python
@timeout(3, 3)
def get_relation(tenant_id, kb_id, from_ent_name, to_ent_name, size=1):
    # 每次调用都是一次ES查询
    conds = {"fields": ["content_with_weight"], "size": size, 
             "from_entity_kwd": ents, "to_entity_kwd": ents, 
             "knowledge_graph_kwd": ["relation"]}
    es_res = settings.retriever.search(conds, search.index_name(tenant_id), [kb_id])
```

**影响**: 
- 对于top_n个关系(默认6个),可能产生6次额外的ES查询
- 如果有多个tenant,查询次数会更多

---

### 🟢 轻微问题 6: N-hop路径计算复杂度

**位置**: `graphrag/search.py` 第170-185行

**问题代码**:
```python
nhop_pathes = defaultdict(dict)
for _, ent in ents_from_query.items():
    nhops = ent.get("n_hop_ents", [])
    if not isinstance(nhops, list):
        logging.warning(f"Abnormal n_hop_ents: {nhops}")
        continue
    for nbr in nhops:
        path = nbr["path"]
        wts = nbr["weights"]
        # 嵌套循环计算路径权重
        for i in range(len(path) - 1):
            f, t = path[i], path[i + 1]
            if (f, t) in nhop_pathes:
                nhop_pathes[(f, t)]["sim"] += ent["sim"] / (2 + i)
            else:
                nhop_pathes[(f, t)]["sim"] = ent["sim"] / (2 + i)
            nhop_pathes[(f, t)]["pagerank"] = wts[i]
```

**影响**: 
- 三层嵌套循环
- 对于复杂图谱,计算量可能较大

---

## 性能影响量化估算

假设一次知识图谱检索的时间分布:

| 环节 | 耗时估算 | 占比 |
|------|---------|------|
| LLM查询重写 | 1-3秒 | 30-40% |
| 获取实体类型样本(10000条) | 0.5-1秒 | 10-15% |
| 实体关键词向量化 | 0.2-0.5秒 | 5-10% |
| 关系文本向量化 | 0.2-0.5秒 | 5-10% |
| ES实体检索(N=56) | 0.3-0.5秒 | 5-10% |
| ES关系检索(N=56) | 0.3-0.5秒 | 5-10% |
| ES类型实体检索(N=10000) | 0.5-1秒 | 10-15% |
| 关系描述补充查询(6次) | 0.3-0.6秒 | 5-10% |
| N-hop路径计算 | 0.1-0.2秒 | 2-5% |
| 社区检索 | 0.2-0.3秒 | 3-5% |

**单次检索总耗时**: 约3.6-8.1秒

**由于重复调用问题**: 实际耗时 = 3.6-8.1秒 × 2 = **7.2-16.2秒**

---

## 优化建议

### 🎯 高优先级优化

#### 1. 修复重复调用问题 (预期提升50%)

**修改文件**: `agent/tools/retrieval.py` 和 `docker/local_codes/agent/tools/retrieval.py`

删除第173-178行的重复代码,只保留第162-169行的调用。

#### 2. 优化LLM查询重写 (预期提升20-30%)

**方案A**: 添加查询缓存
```python
def query_rewrite(self, llm, question, idxnms, kb_ids):
    # 添加查询级别的缓存
    cache_key = f"qr_{hash(question)}_{','.join(kb_ids)}"
    cached = get_query_rewrite_cache(cache_key)
    if cached:
        return cached
    
    ty2ents = trio.run(lambda: get_entity_type2samples(idxnms, kb_ids))
    # ... 其余逻辑
    set_query_rewrite_cache(cache_key, result)
```

**方案B**: 减少实体类型样本数量
```python
# 从10000减少到1000或更少
es_res = await trio.to_thread.run_sync(lambda: settings.retriever.search({
    "knowledge_graph_kwd": "ty2ents", 
    "kb_id": kb_ids, 
    "size": 1000,  # 从10000减少
    "fields": ["content_with_weight"]
}, idxnms, kb_ids))
```

#### 3. 减少类型实体检索数量 (预期提升10-15%)

```python
# 从10000减少到100-500
ents_from_types = self.get_relevant_ents_by_types(ty_kwds, filters, idxnms, kb_ids, 100)
```

### 🎯 中优先级优化

#### 4. 批量获取关系描述

将循环查询改为批量查询:
```python
# 收集所有需要查询的关系
missing_rels = [(f, t) for (f, t), rel in rels_from_txt if not rel.get("description")]

# 批量查询
if missing_rels:
    batch_rels = batch_get_relations(tenant_ids, kb_ids, missing_rels)
    for (f, t), rel in rels_from_txt:
        if not rel.get("description") and (f, t) in batch_rels:
            rel["description"] = batch_rels[(f, t)]["description"]
```

#### 5. 向量化批处理

将多次向量化合并为一次:
```python
# 合并需要向量化的文本
texts_to_embed = [", ".join(ents), qst]
embeddings = emb_mdl.encode_batch(texts_to_embed)

# 使用预计算的向量
ents_from_query = self.get_relevant_ents_by_keywords_with_vector(
    embeddings[0], filters, idxnms, kb_ids, ent_sim_threshold)
rels_from_txt = self.get_relevant_relations_by_txt_with_vector(
    embeddings[1], filters, idxnms, kb_ids, rel_sim_threshold)
```

### 🎯 低优先级优化

#### 6. 异步并行执行

将串行的ES查询改为并行:
```python
# 使用trio并行执行
async with trio.open_nursery() as nursery:
    nursery.start_soon(get_relevant_ents_by_keywords_async, ...)
    nursery.start_soon(get_relevant_ents_by_types_async, ...)
    nursery.start_soon(get_relevant_relations_by_txt_async, ...)
```

#### 7. 添加监控和日志

在关键环节添加性能监控:
```python
import time

def retrieval(self, question, ...):
    start_time = time.time()
    
    # 查询重写
    rewrite_start = time.time()
    ty_kwds, ents = self.query_rewrite(llm, qst, idxnms, kb_ids)
    logging.info(f"Query rewrite took: {time.time() - rewrite_start:.2f}s")
    
    # 实体检索
    ent_start = time.time()
    ents_from_query = self.get_relevant_ents_by_keywords(...)
    logging.info(f"Entity retrieval took: {time.time() - ent_start:.2f}s")
    
    # ... 其他环节
    
    logging.info(f"Total KG retrieval took: {time.time() - start_time:.2f}s")
```

---

## 总结

**主要性能瓶颈排序**:
1. ⭐⭐⭐ 重复调用知识图谱检索 (影响最大,修复最简单)
2. ⭐⭐⭐ LLM查询重写开销 (耗时长,优化空间大)
3. ⭐⭐ 大量实体类型检索 (N=10000)
4. ⭐⭐ 多次向量化计算
5. ⭐ 关系描述的循环查询
6. ⭐ N-hop路径计算

**预期优化效果**:
- 修复重复调用: **性能提升50%**
- 优化LLM查询重写: **性能提升20-30%**
- 其他优化: **性能提升10-20%**

**总体预期**: 通过以上优化,知识图谱检索性能可提升 **70-80%**,响应时间从7-16秒降低到 **2-4秒**。

