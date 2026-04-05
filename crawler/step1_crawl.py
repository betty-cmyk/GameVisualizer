# -*- coding: utf-8 -*-
import sqlite3, json, time, urllib.request, urllib.parse, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
TEMP_JSON = ROOT / "data" / "temp_raw_cited.json"
POLITE_EMAIL = "1439461425@qq.com"
API_BASE = "https://api.openalex.org/works"

def get_citing_works(oa_id):
    clean_id = str(oa_id).split('/')[-1]
    query = urllib.parse.urlencode({
        "filter": f"cites:{clean_id}", 
        "sort": "cited_by_count:desc",
        "per-page": 25,
        "mailto": POLITE_EMAIL
    })
    url = f"{API_BASE}?{query}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamePaperVisualizer/3.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8')).get('results', [])
    except Exception as e:
        if "429" in str(e): return "RATE_LIMIT"
        print(f"    [x] API 请求失败: {str(e)}")
    return []

def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # 放宽扩张门槛：不再苛求 Tier S/A，只要引用 > 20 次且拥有 OpenAlex ID 即可作为向外扩张的星系引擎！
    cur.execute("""
        SELECT title, openalex_id, category_9, citations 
        FROM papers 
        WHERE openalex_id IS NOT NULL AND openalex_id != 'NOT_FOUND' AND openalex_id != ''
        AND citations >= 20 
        ORDER BY citations DESC LIMIT 100
    """)
    hubs = cur.fetchall()
    
    cur.execute("SELECT LOWER(title) FROM papers")
    existing_titles = set([r[0] for r in cur.fetchall() if r[0]])
    conn.close()
    
    print(f"\n=== Step 1: 启动深空爬虫 (从 {len(hubs)} 个顶级枢纽向外派生) ===")
    raw_papers = []
    
    for title, oa_id, cat, cites in hubs:
        print(f"\n[*] 扫描枢纽: {title[:50]}... (被引: {cites})")
        works = get_citing_works(oa_id)
        
        if works == "RATE_LIMIT":
            print("    [!] 触发频率限制，挂起 30 秒...")
            time.sleep(30)
            continue
            
        if not works: continue
            
        added = 0
        for w in works:
            w_title = w.get('title')
            if not w_title: continue
            
            clean_title = w_title.lower().strip()
            if clean_title in existing_titles: continue
            
            w_cites = w.get('cited_by_count', 0)
            w_oa_id = w.get('id', '')
            w_year = w.get('publication_year', 0)
            w_doi = w.get('doi', '')
            
            authors = [a.get('author', {}).get('display_name', '') for a in w.get('authorships', [])]
            w_author = ' / '.join([a for a in authors if a][:3])
            if len(authors) > 3: w_author += " et al."
            
            w_abstract = ""
            idx_abs = w.get('abstract_inverted_index', {})
            if idx_abs:
                word_index = [(p, word) for word, pos_list in idx_abs.items() for p in pos_list]
                word_index.sort(key=lambda x: x[0])
                w_abstract = " ".join([x[1] for x in word_index])
            
            refs = [r.split('/')[-1] for r in w.get('referenced_works', []) if r]
            w_ref_json = json.dumps(refs)
            
            raw_papers.append({
                'title': w_title, 'author': w_author, 'year': w_year, 
                'directions': cat, 'category_9': cat, 'abstract': w_abstract, 
                'citations': w_cites, 'openalex_id': w_oa_id, 
                'references_list': w_ref_json, 'doi': w_doi
            })
            existing_titles.add(clean_title)
            added += 1
            
        if added > 0: print(f"    [+] 捕获 {added} 颗卫星节点")
        time.sleep(1.2)
        
    TEMP_JSON.write_text(json.dumps(raw_papers, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n[OK] Step 1 结束！共抓取 {len(raw_papers)} 篇野生原始文献，已暂存至 {TEMP_JSON.name}。")

if __name__ == '__main__':
    main()
