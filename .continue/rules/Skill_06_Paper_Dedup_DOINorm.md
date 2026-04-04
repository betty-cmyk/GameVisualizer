# Skill 06：论文主键归一与去重（DOI/arXiv/Title）

**Tags:** `#dedup #doi #arxiv #metadata #normalization`

## L0 决策卡（30 秒）

- 多源抓取后重复很多？→ 启用主键级去重
- DOI 缺失但标题高度相似？→ 标题归一 + 年份兜底
- 需要低上下文执行？→ 只跑 L1 的三段规则

## L1 标准流程（最小执行）

### 1) 主键优先级

1. `doi_norm`（最强）
2. `arxiv_id_norm`
3. `title_norm + year`

### 2) 归一规则

- DOI：小写、去前缀（`https://doi.org/`、`doi:`）
- arXiv：提取核心 ID（如 `2401.01234`）
- 标题：小写、去标点、压缩空白、统一连字符

### 3) 合并策略

- 同主键多记录时，保留“信息最全”一条
- 字段补全采用并集：`url/abstract/keywords/venue`
- 记录 `source_count` 与 `source_list`

## L2 故障处理

- 无 DOI/arXiv：启用 `title_norm + year`，并加相似度二次判定
- 同名不同文：若作者差异大且 venue 不同，标记为冲突人工复核
- 年份缺失：允许 `title_norm` 暂存，后续回填年份再决策

## 最小输入字段

- `title`
- `year`
- `doi`（可空）
- `arxiv_id`（可空）
- `authors`
- `venue`

## 成功判定

- 重复率显著下降
- 主键冲突率可追踪
- 合并后记录信息不丢失



