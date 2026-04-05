# -*- coding: utf-8 -*-
import sqlite3, json, urllib.request, urllib.parse, concurrent.futures
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"
FILTERED_JSON = ROOT / "data" / "temp_filtered_cited.json"

def translate_text(text):
    if not text: return ""
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return ''.join([sentence[0] for sentence in result[0]])
    except:
        return ""

def main():
    if not FILTERED_JSON.exists():
        print("Error: temp_filtered_cited.json 不存在！请先运行 step2_filter.py")
        return

    clean_papers = json.loads(FILTERED_JSON.read_text(encoding='utf-8'))
    if not clean_papers:
        print("[!] 待翻译队伍为空！直接结束。")
        return

    print(f"\n=== Step 3.1: 启动 {len(clean_papers)} 篇待命卫星的量子翻译机 ===")
    
    def do_trans(p):
        zh = translate_text(p['title'])
        p['title_zh'] = zh
        return p
        
    translated_papers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for i, res in enumerate(executor.map(do_trans, clean_papers)):
            translated_papers.append(res)
            if (i+1) % 10 == 0: print(f"    [~] 已翻译 {i+1}/{len(clean_papers)}...")

    print("\n=== Step 3.2: 安全降落入库与 JSON 同步 ===")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    for p in translated_papers:
        # 避免并发产生的死锁或并发递增失败：每一行写入时都查一次最高的 ID 确保绝对安全！
        cur.execute("SELECT MAX(id) FROM papers")
        safe_id = (cur.fetchone()[0] or 10000) + 1
        
        cur.execute("""
            INSERT INTO papers (id, title, title_zh, author, year, directions, category_9, abstract, citations, tier, openalex_id, references_list, doi, db_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (safe_id, p['title'], p.get('title_zh',''), p['author'], p['year'], p['directions'], p['category_9'], p['abstract'], p['citations'], p['tier'], p['openalex_id'], p['references_list'], p['doi'], 'OpenAlex_Expansion_v3'))
        
    conn.commit()
    
    cur.execute("PRAGMA table_info(papers)")
    cols = [d[1] for d in cur.fetchall()]
    cur.execute("SELECT * FROM papers")
    
    data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
    data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
    JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    conn.close()
    
    # 删掉两个临时文件以保证空间纯洁
    Path(ROOT / "data" / "temp_raw_cited.json").unlink(missing_ok=True)
    Path(ROOT / "data" / "temp_filtered_cited.json").unlink(missing_ok=True)
    
    print(f"\n[OK] 伟大航路全链路宣告竣工！共计 {len(translated_papers)} 颗卫星被永久挂载到你的暗物质图谱中！")
    print("[*] 正在自动为你重新编译最新 D3 宇宙图谱......")

if __name__ == '__main__':
    main()
