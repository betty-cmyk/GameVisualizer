# -*- coding: utf-8 -*-
import sqlite3, json, time, urllib.request, urllib.parse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"

POLITE_EMAIL = "1439461425@qq.com"
API_BASE = "https://api.openalex.org/works"

def safe_print(text):
    clean = text.encode('gbk', 'ignore').decode('gbk')
    print(clean)

def get_openalex_data(title):
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title).strip().lower()
    clean_title = " ".join(clean_title.split()[:10])
    if len(clean_title) < 10: return None
        
    query = urllib.parse.urlencode({"search": clean_title, "mailto": POLITE_EMAIL})
    url = f"{API_BASE}?{query}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamePaperVisualizer/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get('results', [])
            if not results: return None
                
            best_match = results[0]
            api_title = (best_match.get('title') or "").lower()
            api_title_clean = re.sub(r'[^a-z0-9]', '', api_title)
            local_title_clean = re.sub(r'[^a-z0-9]', '', title.lower())
            
            if local_title_clean in api_title_clean or api_title_clean in local_title_clean or \
               (len(local_title_clean)>10 and len(api_title_clean)>10 and len(set(local_title_clean)&set(api_title_clean))/max(len(local_title_clean),len(api_title_clean)) > 0.6):
                return best_match
    except Exception as e:
        if "429" in str(e): return "RATE_LIMIT"
    return None

def main():
    if not DB_PATH.exists(): return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    for col in ['openalex_id', 'references_list', 'cited_by_api']:
        try: cur.execute(f"ALTER TABLE papers ADD COLUMN {col} TEXT")
        except: pass

    cur.execute("SELECT id, title FROM papers WHERE (openalex_id IS NULL OR openalex_id = '') AND title NOT GLOB '*[\u4e00-\u9fa5]*' LIMIT 1500")
    rows = cur.fetchall()
    if not rows:
        safe_print("\n[*] 全库所有英文文献均已完成 OpenAlex 全球引用数据对接！")
        return

    safe_print(f"\n--- OpenAlex 引用网络深度映射启动 (待处理 {len(rows)} 篇) ---")
    
    updated = 0
    for pid, title in rows:
        safe_print(f"\n[*] 扫描: {title[:70]}...")
        oa_data = get_openalex_data(title)
        
        if oa_data == "RATE_LIMIT":
            safe_print("    [🚨] 触发 OpenAlex 频率限制！挂起 30 秒...")
            time.sleep(30)
            continue
            
        if not oa_data:
            safe_print("    [-] 未找到高匹配度文献。标记为 NOT_FOUND。")
            cur.execute("UPDATE papers SET openalex_id=? WHERE id=?", ('NOT_FOUND', pid))
            conn.commit()
        else:
            oa_id = oa_data.get('id', '')
            references = [r.split('/')[-1] for r in oa_data.get('referenced_works', []) if r]
            ref_json = json.dumps(references)
            cited_by = oa_data.get('cited_by_count', 0)
            
            safe_print(f"    [+] 匹配成功! OA-ID: {oa_id.split('/')[-1]} | 引用 {len(references)} 篇 | 被引 {cited_by} 次")
            
            cur.execute("UPDATE papers SET openalex_id=?, references_list=?, cited_by_api=? WHERE id=?", 
                        (oa_id, ref_json, cited_by, pid))
            cur.execute("UPDATE papers SET citations=? WHERE id=? AND citations < ?", (cited_by, pid, cited_by))
            conn.commit()
            updated += 1
            
        time.sleep(1.5)

    safe_print(f"\n[!] 任务结束！本次成功为 {updated} 篇论文绑定了全球引用关系网。")
    if updated > 0:
        cur.execute("PRAGMA table_info(papers)")
        cols = [d[1] for d in cur.fetchall()]
        cur.execute("SELECT * FROM papers")
        data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
        data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
        JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        safe_print("    [+] 数据库已同步至前端 JSON。")

    conn.close()

if __name__ == '__main__': main()