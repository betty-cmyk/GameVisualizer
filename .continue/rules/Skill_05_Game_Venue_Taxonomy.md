# Skill 05：游戏领域分类与会议信号（Venue & Taxonomy）

**Tags:** `#games #taxonomy #venues #survey #classification`

## L0 决策卡（30 秒）

- 你在“扩展全游戏领域”但分类混乱？→ 先做 taxonomy
- 你不确定论文质量层级？→ 先做 venue 分级
- 你要控制上下文长度？→ 只保留 L1 的字段表

## L1 标准流程（最小执行）

### 1) 先定一级分类（固定 8 类）

- Game AI（行为/规划/强化学习）
- PCG（程序化内容生成）
- Rendering（实时渲染/NPR/全局光照）
- Animation（角色动画/运动合成）
- Simulation & Physics（布料/流体/刚体）
- HCI/UX in Games（交互与可用性）
- Networking & Systems（多人同步/性能）
- Serious Games / Game Analytics

### 2) 再定二级标签（每篇最多 3 个）

- 方法标签：`diffusion` `rl` `transformer` `inverse-rendering` ...
- 任务标签：`pathfinding` `style-transfer` `npc-dialogue` ...
- 资产标签：`terrain` `animation` `shader` `level`

### 3) Venue 分级（轻量）

- A：SIGGRAPH / TOG / IEEE TVCG / CVPR/ICCV/ECCV（相关方向）
- B：MIG / CHI PLAY / FDG / AIIDE / SCA
- C：Workshop / arXiv / tech report

## L2 故障处理

- 类别过细：先回收为 8 个一级类，再二级补充
- 交叉归类冲突：主类唯一，副类最多 2 个
- 会议名噪声：用 venue 词典标准化（别名映射）

## 最小输入字段

- `title`
- `venue`
- `year`
- `abstract`
- `keywords`

## 成功判定

- 每篇论文都有且只有 1 个一级分类
- 二级标签平均 2~3 个
- 按 venue 分层后可直接筛选高质量子集



