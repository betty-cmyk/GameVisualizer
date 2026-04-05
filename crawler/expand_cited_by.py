# -*- coding: utf-8 -*-
import sqlite3, json, time, urllib.request, urllib.parse, re, os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"

POLITE_EMAIL = "1439461425@qq.com"
API_BASE = "https://api.openalex.org/works"

def safe_print(text):
    clean = text.encode('gbk', 'ignore').decode('gbk')
    print(clean)

def get_citing_works(oa_id):
    # 获取所有引用了 oa_id 的论文，按被引量排序，取前 20 篇最高质量的
    clean_id = str(oa_id).split('/')[-1]
    query = urllib.parse.urlencode({
        "filter": f"cites:{clean_id}", 
        "sort": "cited_by_count:desc",
        "per-page": 20,
        "mailto": POLITE_EMAIL
    })
    url = f"{API_BASE}?{query}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamePaperVisualizer/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('results', [])
    except Exception as e:
        if "429" in str(e): return "RATE_LIMIT"
        safe_print(f"    [x] API 错误: {str(e)}")
    return []

def main():
    if not DB_PATH.exists(): 
        safe_print("数据库不存在！")
        return
        
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    
    # 1. 寻找扩张源：只找图形学/游戏核心领域的、已被 OpenAlex 收录的、被引量较高的大型枢纽论文
    cur.execute("""
        SELECT id, title, openalex_id, category_9, citations 
        FROM papers 
        WHERE openalex_id IS NOT NULL 
        AND openalex_id != 'NOT_FOUND' 
        AND openalex_id != ''
        AND citations >= 50
        ORDER BY citations DESC 
        LIMIT 50
    """)
    
    hubs = cur.fetchall()
    if not hubs:
        safe_print("没有找到带有 OpenAlex ID 的核心枢纽论文。请先运行 enrich_citations.py！")
        return
        
    safe_print(f"\n--- 启动被引网络辐射式扩张 (选择最核心的 {len(hubs)} 篇论文作为扩张源) ---")
    
    # 获取当前已有标题用于查重
    cur.execute("SELECT LOWER(title) FROM papers")
    existing_titles = set([r[0] for r in cur.fetchall() if r[0]])
    
    # 获取当前最大 ID
    cur.execute("SELECT MAX(id) FROM papers")
    max_id = cur.fetchone()[0] or 10000
    next_id = max_id + 1
    
    new_papers_count = 0
    
    for pid, title, oa_id, cat, cites in hubs:
        safe_print(f"\n[*] 辐射源: {title[:60]}... (当前总被引: {cites})")
        
        works = get_citing_works(oa_id)
        if works == "RATE_LIMIT":
            safe_print("    [!] 触发 OpenAlex 频率限制！挂起 30 秒...")
            time.sleep(30)
            continue
            
        if not works:
            safe_print("    [-] 没有找到引用了它的高质量衍生论文。")
            time.sleep(1)
            continue
            
        added_for_this_hub = 0
        for w in works:
            w_title = w.get('title')
            if not w_title: continue
            
            clean_title = w_title.lower().strip()
            if clean_title in existing_titles:
                continue # 已在库中，跳过
                
            # 提取元数据
            w_oa_id = w.get('id', '')
            w_year = w.get('publication_year', 0)
            w_cites = w.get('cited_by_count', 0)
            w_doi = w.get('doi', '')
            
            authors = [a.get('author', {}).get('display_name', '') for a in w.get('authorships', [])]
            w_author = ' / '.join([a for a in authors if a][:3])
            if len(authors) > 3: w_author += " et al."
            
            w_abstract = ""
            idx_abs = w.get('abstract_inverted_index', {})
            if idx_abs:
                # OpenAlex 倒排索引重组摘要
                word_index = []
                for word, pos_list in idx_abs.items():
                    for p in pos_list:
                        word_index.append((p, word))
                word_index.sort(key=lambda x: x[0])
                w_abstract = " ".join([x[1] for x in word_index])
            
            # 这篇论文既然引用了枢纽论文，那它大概率也属于这个分类。为了不抢枢纽的风头，打上 Tier B/C
            w_tier = 'B' if w_cites > 20 else 'C'
            
            # 它引用的参考文献列表 (为了能跟库里别的论文连起来)
            refs = [r.split('/')[-1] for r in w.get('referenced_works', []) if r]
            w_ref_json = json.dumps(refs)
            
            # 插入数据库
            cur.execute("""
                INSERT INTO papers (id, title, author, year, directions, category_9, abstract, citations, tier, openalex_id, references_list, doi, db_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (next_id, w_title, w_author, w_year, cat, cat, w_abstract, w_cites, w_tier, w_oa_id, w_ref_json, w_doi, 'OpenAlex_Expansion'))
            
            existing_titles.add(clean_title)
            next_id += 1
            new_papers_count += 1
            added_for_this_hub += 1
            
        if added_for_this_hub > 0:
            conn.commit()
            safe_print(f"    [+] 成功为该枢纽补充了 {added_for_this_hub} 篇外部高质量引用卫星节点！")
            
        time.sleep(1.5)

    safe_print(f"\n[!] 扩张行动结束！共向宇宙中注入了 {new_papers_count} 颗全新的卫星节点。")
    
    if new_papers_count > 0:
        cur.execute("PRAGMA table_info(papers)")
        cols = [d[1] for d in cur.fetchall()]
        cur.execute("SELECT * FROM papers")
        
        data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
        data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
        JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        safe_print("    [+] SQLite 数据库已成功同步至 papers_clean.json！")

    conn.close()

if __name__ == '__main__':
    main()
