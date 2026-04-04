# Skill Router（最小上下文入口）

> 目标：**分层分级 + 最小加载**。每次只加载 1 个主 Skill，最多附加 1 个辅助 Skill。

## L0：任务分流（先选一个）

- 反爬、验证码、浏览器接管 → `Skill_01_Web_Scraping_Anti_Bot.md`
- Windows/PowerShell 命令异常、编码、代理问题 → `Skill_02_Windows_PowerShell_Pitfalls.md`
- SQLite/JSON 清洗、去重、同步、恢复 → `Skill_03_SQLite_Data_Cleaning.md`
- Cursor 代码改写策略、避免补丁污染 → `Skill_04_Cursor_Agent_Guidelines.md`
- 游戏论文的领域划分与会议分层 → `Skill_05_Game_Venue_Taxonomy.md`
- 跨源论文主键归一与去重合并 → `Skill_06_Paper_Dedup_DOINorm.md`
- Skill 分级调用与最小上下文约束 → `Skill_98_Invoke_Policy.md`

## 加载策略（减少上下文）

1. 只读「L0 决策卡 + L1 标准流程」
2. 失败时再读「L2 故障处理」
3. 不跨技能复制整段案例；只抄命令模板

## 统一输出模板（建议）

- 当前选择 Skill：
- 当前层级：L0 / L1 / L2
- 本轮输入最小字段：
- 执行动作（3 步内）：
- 成功判定：
- 回滚方案：


