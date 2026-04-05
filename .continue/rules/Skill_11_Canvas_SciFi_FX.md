# Skill 11：Canvas 科幻光影与图层性能戒律 (Sci-Fi Canvas FX & Performance)
**Tags:** `#canvas #animation #performance #ghosting`

## 痛点与血泪教训
1. **灾难级的双重漂移 (Matrix Ghosting)**：在 `render()` 循环内，如果 `ctx.save()` 和 `ctx.restore()` 没有完美闭合，或者错误地嵌套了两次 `ctx.translate/scale`，会导致图形在拖拽时以二次方速度飞出屏幕，并留下极其恐怖的重影和残影。
2. **GPU 算力暴毙**：不要每一帧都去画几万条背景连线，或者在极高倍缩小（如 `transform.k < 0.2`）时去渲染超大模糊半径（`shadowBlur = 18 / k` 会膨胀到 100px+）的高斯阴影。

## L1 极客光流特效：学术脉冲射线 (Pulse Flow)
在展示 `citeEdges`（学术引用红紫射线）时，摒弃死板的静态箭头，使用带有时间戳的高能虚线流动来直观展示**知识的影响方向**：
```javascript
// 利用 Date.now() 制造流光虚线偏移特效，负数代表向目标疯狂流动
const timeOffset = (Date.now() / 30) % 50;
ctx.setLineDash([15 / transform.k, 15 / transform.k]); // 15px发光实线，15px暗区
ctx.lineDashOffset = -timeOffset / transform.k;
ctx.shadowColor = color;
ctx.shadowBlur = 8 / transform.k; // 霓虹发光
```
**按需调度 (`requestAnimationFrame`)**：只有在选中节点且处于 `cite` 模式时，才开启 60 帧动画循环；平时静默态只需响应 `d3.zoom` 拖拽，保证极致省电。

## L2 高清渲染图层戒律 (Render Pipeline)
一个完美无重影的 Canvas 渲染流必须严格遵循：
1. **清屏并锁定物理视口**：开局 `ctx.setTransform(dpr, 0, 0, dpr, 0, 0)` 配合 `fillRect` 涂黑。
2. **特效底层 (Screen)**：单独开一个 `save/translate/scale` 矩阵，用 `globalCompositeOperation = 'screen'` 画 8 大分类的渐变光环，画完立刻 `restore`。
3. **实体主层 (Source-Over)**：再开一个干净的 `save/translate/scale` 矩阵，以此顺序画：背景极弱白丝连线 -> 选中时的高亮射线 -> 论文光点。画完后 `restore`。
4. **绝对物理层 (UI Labels)**：最后在没有任何缩放矩阵的保护下，计算真实的屏幕物理坐标（`n.x * k + tx`），利用 8 方向螺旋探测防遮挡算法画极客文字标签。