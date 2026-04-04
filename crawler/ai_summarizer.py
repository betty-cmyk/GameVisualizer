# -*- coding: utf-8 -*-
import sqlite3, json, time, os, re
import urllib.request
from pathlib import Path

# --- 请在这里填入你的 DeepSeek API Key ---
API_KEY = "在此处填入你的_DEEPSEEK_API_KEY"
API_URL = "https://api.deepseek.com/chat/completions"
DB_PATH = Path("data/papers.db")
JSON_CLEAN = Path("data/papers_clean.json")

SYSTEM_PROMPT = """你是一位专业的计算机图形学与游戏科学专家。请根据提供的论文摘要，生成一个约200字的中文深度总结。
总结必须包含以下五个维度，并使用清晰的加粗标题：
1. 【研究问题】：这篇论文试图解决什么核心痛点？
2. 【创新点】：采用了什么新颖的方法或架构？
3. 【研究方法】：简述实验或算法流程。
4. 【研究结论】：最终达到了什么效果或性能指标？
5. 【启发价值】：对现代游戏设计或开发（如引擎渲染、NPC交互、性能优化等）有何具体参考价值？
"""

def call_deepseek(abstract):
    if "填入" in API_KEY:
        print("  [!] 错误：请先在脚本中填入有效的 DeepSeek API Key！")
        return None
        
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请总结这篇论文：{abstract}"}
        ],
        "temperature": 0.3
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"  [!] API 调用失败: {e}")
        return None

def main():
    if not DB_PATH.exists(): return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 查找有摘要但还没有 AI 总结的论文
    cur.execute("SELECT id, title, abstract FROM papers WHERE abstract IS NOT NULL AND length(abstract) > 50 AND (ai_summary IS NULL OR ai_summary = '') LIMIT 10")
    rows = cur.fetchall()
    
    if not rows:
        print("--- 所有待处理论文均已完成 AI 总结 ---")
        return

    print(f"--- 正在为 {len(rows)} 篇论文生成 AI 深度总结 --- ")

    count = 0
    for pid, title, abstract in rows:
        print(f"\n[*] 正在总结 ({count+1}/{len(rows)}): {title[:30]}...")
        
        ai_res = call_deepseek(abstract)
        if ai_res:
            cur.execute("UPDATE papers SET ai_summary=? WHERE id=?", (ai_res, pid))
            conn.commit()
            count += 1
            print(f"  [+] 总结生成成功")
            time.sleep(1)
        else:
            print("  [-] 本条总结生成失败")

    if count > 0:
        print("\n[*] 正在同步数据至 papers_clean.json...")
        cur.execute("PRAGMA table_info(papers)")
        cols = [d[1] for d in cur.fetchall()]
        cur.execute("SELECT * FROM papers")
        all_p = [dict(zip(cols, r)) for r in cur.fetchall()]
        JSON_CLEAN.write_text(json.dumps({'total': len(all_p), 'papers': all_p}, ensure_ascii=False, indent=2), encoding='utf-8')
        print("--- 总结任务阶段性完成 ---")

    conn.close()

if __name__ == "__main__":
    main()