# -*- coding: utf-8 -*-
import sqlite3, json, time, urllib.request, urllib.parse, re, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"

UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
]

def safe_print(text):
    clean = text.encode('gbk', 'ignore').decode('gbk')
    print(clean)

def translate_google(text):
    if not text or len(text) < 3: return text
    text = text.replace('\n', ' ').strip()
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text)
    headers = {'User-Agent': random.choice(UAS)}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            zh_text = "".join([item[0] for item in res[0] if item[0]])
            zh_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_ \.,;:!\?\-\'"\(\)\[\]]', '', zh_text)
            return zh_text
    except Exception as e:
        return str(e)

def main():
    if not DB_PATH.exists(): return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    try: cur.execute("ALTER TABLE papers ADD COLUMN title_zh TEXT")
    except: pass

    cur.execute("SELECT id, title FROM papers WHERE (title_zh IS NULL OR title_zh = '') AND title NOT GLOB '*[\u4e00-\u9fa5]*' LIMIT 1500")
    rows = cur.fetchall()
    
    if not rows:
        safe_print("\n[*] 所有文献标题均已完成中文翻译！")
        return

    safe_print(f"\n--- 全量翻译引擎启动 (待处理 {len(rows)} 篇) ---")
    
    updated = 0
    for pid, title in rows:
        safe_print(f"\n[EN] {title[:80]}")
        zh_title = translate_google(title)
        
        if zh_title and "HTTP Error" not in zh_title:
            safe_print(f"[ZH] {zh_title[:80]}")
            cur.execute("UPDATE papers SET title_zh=? WHERE id=?", (zh_title, pid))
            conn.commit()
            updated += 1
        else:
            safe_print(f"[-] 翻译被拦截或失败: {zh_title}。脚本将挂起等待 60 秒...")
            time.sleep(60)
            continue
            
        time.sleep(random.uniform(2.5, 4.5))

    if updated > 0:
        safe_print("\n[*] 正在同步全量中英双语数据至 JSON...")
        cur.execute("PRAGMA table_info(papers)")
        cols = [d[1] for d in cur.fetchall()]
        cur.execute("SELECT * FROM papers")
        data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
        data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
        JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        safe_print(f"\n[!] 完美收官！成功翻译 {updated} 篇文献并发布到图谱。")

    conn.close()

if __name__ == '__main__': main()