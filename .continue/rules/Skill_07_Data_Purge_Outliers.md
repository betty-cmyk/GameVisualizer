# Skill 07：跨界毒瘤过滤与视觉物理降维 (Outlier Purge & Tier-First Physics)
**Tags:** `#data-cleaning #d3-physics #outliers #tier-first`

## 痛点与血泪教训
不要信任爬虫带来的全网超高引用数据。如《两点地震射线追踪》虽含 "Ray tracing"，但属于地震学，高达 900+ 被引。若不加干预，它们会：
1. 破坏 `maxCites` 的比例，导致正常图形学论文尺寸剧变。
2. 因为体积过于庞大，产生超强物理斥力 (`forceCollide`)，把自己弹射到图谱的真空边缘。

## L1 免疫法则：后端生成级斩杀
在任何生成 JSON 图谱数据的脚本 (如 `gen_graph_v3.py`) 的主循环中，**强制硬编码过滤**：
```python
# 过滤法则：非图形学顶会 (非S/A) 且引用量异常畸高 (>150)，直接判定为跨界污染
if tier not in ('S', 'A') and cites > 150:
    continue
```

## L2 视觉法则：绝对阶级控制
前端 D3 的节点大小 `n.r` 与发光度 `alpha`，**必须以评级 (Tier) 为第一优先**。
- Tier S 最大封顶必须限制在屏幕视觉的绝对核心范围。
- 严禁采用全局被引统一映射公式，必须分段 `baseR + maxBonus` 计算。