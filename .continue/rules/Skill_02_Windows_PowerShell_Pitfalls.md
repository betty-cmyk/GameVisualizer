# Skill 02：Windows 与 PowerShell 避坑

**Tags:** `#windows #powershell #terminal #encoding #env`

## L0 决策卡（30 秒）

- 多命令执行失败？先看命令连接符
- 日志报编码错？先看控制台字符集
- pip 失败且代理相关？先清代理变量

## L1 标准流程（最小执行）

### 1) 多命令用 `;`（而非盲目 `&&`）

```powershell
python a.py; python b.py
```

### 2) 长脚本不要 `python -c` 地狱转义

- 复杂逻辑一律落 `.py` 文件再执行

### 3) pip 安装先清代理

```cmd
set HTTP_PROXY=
set HTTPS_PROXY=
pip install selenium -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## L2 故障处理

- `UnicodeEncodeError`：日志去 emoji/非常规字符，仅保留 ASCII 标记
- `CommandNotFound/ParserError`：先确认 shell 是 PowerShell 还是 CMD
- 命令很长：改脚本文件，避免多层引号

## 最小输入字段

- 当前 shell（PowerShell/CMD）
- 报错原文（前后 5 行）
- 复现命令
