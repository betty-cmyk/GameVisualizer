# Skill 03：SQLite 数据清洗与同步

**Tags:** `#sqlite #database #json #data-cleaning #sync`

## L0 决策卡（30 秒）

- 要删除/更新多行？先 `SELECT count(*)` 预演
- 数据不可重爬？优先保留 JSON 备份
- 图谱边太稀疏？检查关键词缺失率

## L1 标准流程（最小执行）

### 1) 高风险 SQL 前置预演

```sql
SELECT count(*) FROM papers WHERE ...;
```

### 2) 去重规则

- 主键：标准化标题（去空格/大小写归一）
- 保留：信息更完整记录（URL/摘要/关键词优先）

### 3) 双向同步

- DB 为结构化主库
- JSON 为可恢复快照 + 前端输入

## L2 故障处理

- 误删：用 JSON 重建 DB（recover 脚本）
- 年份类型错：统一 `str/int` 兼容转换
- 关键词缺失：从标题/摘要词表反补，提升连边质量

## 最小输入字段

- `title/year/url/abstract/keywords`
- 清洗规则版本号

## 成功判定

- 无异常年份、乱码标题
- 重复标题可控
- 图谱连边密度达到目标
