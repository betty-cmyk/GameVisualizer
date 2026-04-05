# Skill 09：图谱宇宙扩张与并发数据安全 (Universal Expansion & Data Integrity)
**Tags:** `#python #sqlite #concurrency #openalex #data-pipeline`

## 痛点与血泪教训
在向图谱中批量注入成百上千篇由 OpenAlex 外部爬取回来的野生派生论文（Cited-by Works）时，极易发生 **SQLite UNIQUE constraint failed (主键碰撞)** 报错。原因在于：多线程翻译（`ThreadPoolExecutor`）打乱了返回顺序，若在并发前预先分配自增 `next_id`，必然导致落地时键值冲突。

## L1 核心数据安全法则：落地前实时取号
**绝对禁止在多线程或并发前人工推算 `next_id`！**
在最终将新生论文写入 `papers.db` 时，必须在执行 `INSERT` 的前一秒，动态查询当前表内的安全最大值：
```python
for p in translated_papers:
    cur.execute("SELECT MAX(id) FROM papers")
    safe_id = (cur.fetchone()[0] or 10000) + 1
    cur.execute("INSERT INTO papers (id, ...) VALUES (?, ...)", (safe_id, ...))
```

## L2 三步解耦架构：爬取、提纯、同步
针对大型外部关联网络的拉取，必须严格切分为三个独立脚本，通过临时 JSON 传递状态，方便断点续传与人工干预：
1. **`step1_crawl.py` (深空爬虫)**：放宽扩张枢纽门槛（被引 > 20），获取派生论文，仅抓取不入库。
2. **`step2_filter.py` (提纯滤网)**：无情斩杀 0 引用废料与被引畸高 (> 250) 的跨界毒瘤，强制赋予其安全层级 `Tier B/C`。
3. **`step3_translate_sync.py` (并发同步)**：多线程调用翻译 API 后，以最安全的 `MAX(id)` 策略无缝缝合至 SQLite 与 `papers_clean.json`。