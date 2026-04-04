# Skill 01：学术站点反爬抓取（Web Scraping Anti-Bot）

**Tags:** `#crawler #python #selenium #anti-bot #academic`

## L0 决策卡（30 秒）

- 目标站点有强反爬（CNKI/学术搜索/验证码）→ 不用纯 requests
- 必须复用真实浏览器态 → 走 CDP 接管
- 触发验证码 → 不抛异常退出，进入等待人工模式

## L1 标准流程（最小执行）

### 1) 启动浏览器调试端口

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug"
```

### 2) Python 接管已登录浏览器

```python
from selenium import webdriver

opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=opts)
```

### 3) 反爬节流（必要）

```python
import random, time

time.sleep(random.uniform(35.0, 65.0))
```

## L2 故障处理（按症状）

- `403/验证码`：检测关键词后循环等待人工通过，不退出
- `NoSuchWindow/Timeout`：优先判断是否被验证页接管，再继续
- 摘要污染（问答文本）：只解析学术 DOM，拒绝通用 snippet

## 最小输入字段

- `query/title`
- `source_site`
- `rate_limit`

## 成功判定

- 链接可回溯到论文详情页
- 摘要不含“问答/关注者/被浏览”等噪声
