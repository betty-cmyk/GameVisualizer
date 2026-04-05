# -*- coding: utf-8 -*-
import sqlite3, json, time, urllib.request, urllib.parse, re, os, concurrent.futures
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"

POLITE_EMAIL = "1439461425@qq.com"
API_BASE = "https://api.openalex.org/works"

def safe_print(text):
    print(text.encode('gbk', 'ignore').decode('gbk'), flush=True)

def get_citing_works(oa_id):
    clean_id = str(oa_id).split('/')[-1]
    query = urllib.parse.urlencode({
        "filter": f"cites:{clean_id}", 
        "sort": "cited_by_count:desc",
        "per-page": 25,  # 每个超级枢纽向外扩展抓取 25 篇最优质的派生论文
        "mailto": POLITE_EMAIL
    })
    url = f"{API_BASE}?{query}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamePaperVisualizer/2.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('results', [])
    except Exception as e:
        if "429" in str(e): return "RATE_LIMIT"
        safe_print(f"    [x] API 请求失败: {str(e)}")
    return []

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
    if not DB_PATH.exists(): return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # =============== 1. 爬取与过滤洗白 (Crawl & Filter) ===============
    cur.execute("""
        SELECT id, title, openalex_id, category_9, citations 
        FROM papers 
        WHERE openalex_id IS NOT NULL AND openalex_id != 'NOT_FOUND' 
        AND citations >= 100 AND tier IN ('S', 'A')
        ORDER BY citations DESC LIMIT 30
    """)
    hubs = cur.fetchall()
    
    cur.execute("SELECT LOWER(title) FROM papers")
    existing_titles = set([r[0] for r in cur.fetchall() if r[0]])
    
    # 废弃人工推算 ID，后续使用 SQLite 自增特性或者插入时动态查询
    
    safe_print(f"\n=== 阶段 1：启动大航海辐射扩张 (从 {len(hubs)} 个顶级枢纽向外派生) ===")
    
    new_papers = []
    
    for pid, title, oa_id, cat, cites in hubs:
        safe_print(f"\n[*] 扫描枢纽: {title[:50]}... (被引: {cites})")
        works = get_citing_works(oa_id)
        
        if works == "RATE_LIMIT":
            safe_print("    [!] 触发 OpenAlex API 频率限制，挂起 30 秒...")
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
            # 【毒瘤拦截】：排除毫无引用的极低质量论文，或者被引畸高的跨界巨怪
            if w_cites < 2 or w_cites > 400: continue
                
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
            
            w_tier = 'B' if w_cites > 30 else 'C'
            refs = [r.split('/')[-1] for r in w.get('referenced_works', []) if r]
            w_ref_json = json.dumps(refs)
            
            new_papers.append({
                'title': w_title, 'author': w_author, 'year': w_year, 
                'directions': cat, 'category_9': cat, 'abstract': w_abstract, 
                'citations': w_cites, 'tier': w_tier, 'openalex_id': w_oa_id, 
                'references_list': w_ref_json, 'doi': w_doi
            })
            existing_titles.add(clean_title)
            added += 1
            
        if added > 0: safe_print(f"    [+] 成功捕获 {added} 颗高质量卫星节点")
        time.sleep(1.2)
        
    if not new_papers:
        safe_print("\n[!] 宇宙已经极其致密，没有发现新的高质量卫星节点。")
        conn.close()
        return

    # =============== 2. 并发智能翻译 (Translate) ===============
    safe_print(f"\n=== 阶段 2：启动 {len(new_papers)} 篇新生论文的量子翻译机 ===")
    
    def do_trans(p):
        zh = translate_text(p['title'])
        p['title_zh'] = zh
        return p
        
    translated_papers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for i, res in enumerate(executor.map(do_trans, new_papers)):
            translated_papers.append(res)
            if (i+1) % 10 == 0: safe_print(f"    [~] 已翻译 {i+1}/{len(new_papers)}...")
            
    # =============== 3. 落地入库 (Sync DB & JSON) ===============
    safe_print("\n=== 阶段 3：星系档案入库与 JSON 同步 ===")
    
    for p in translated_papers:
        cur.execute("SELECT MAX(id) FROM papers")
        current_max = cur.fetchone()[0] or 10000
        safe_id = current_max + 1
        
        cur.execute("""
            INSERT INTO papers (id, title, title_zh, author, year, directions, category_9, abstract, citations, tier, openalex_id, references_list, doi, db_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (safe_id, p['title'], p.get('title_zh',''), p['author'], p['year'], p['directions'], p['category_9'], p['abstract'], p['citations'], p['tier'], p['openalex_id'], p['references_list'], p['doi'], 'OpenAlex_Expansion'))
        
    conn.commit()
    
    cur.execute("PRAGMA table_info(papers)")
    cols = [d[1] for d in cur.fetchall()]
    cur.execute("SELECT * FROM papers")
    
    data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
    data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
    JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    conn.close()
    safe_print(f"\n[OK] 伟大航路任务圆满结束！共计 {len(translated_papers)} 颗带有中英双语与完整引用的卫星被挂载到你的暗物质图谱中！")
    safe_print("[*] 接下来，你可以直接运行 `python crawler/gen_graph_v3.py` 和 `build_site.py` 来重新渲染图谱了！")

if __name__ == '__main__':
    main()
