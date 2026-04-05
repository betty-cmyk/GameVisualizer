import json
import sqlite3
import os

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(CRAWLER_DIR, '..')
DATA_DIR = os.path.join(ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'papers.db')
JSON_PATH = os.path.join(DATA_DIR, 'papers_clean.json')

def main():
    # 1. 打开数据库
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 我们要剔除的垃圾节点特征：不是 S/A，且被引畸高（> 150），或者是跨界词汇
    # 你提到的几个：地震射线追踪、PlenOctrees、ARTS、kd 树等
    cur.execute("""
        SELECT id, title, title_zh, citations, tier, category_9
        FROM papers 
        WHERE tier NOT IN ('S', 'A') 
        AND citations > 150
    """)
    
    outliers = cur.fetchall()
    print(f"[!] Found {len(outliers)} massive Tier-C/null outliers.")
    
    outlier_ids = []
    for r in outliers:
        pid, title, title_zh, cites, tier, cat = r
        # 我们可以根据标题中的跨界词或者纯粹根据 citations 过高且非顶会来过滤
        print(f"- Removing: [{cites}] {title_zh} ({title})")
        outlier_ids.append(pid)
        
    if not outlier_ids:
        print("No outliers to remove.")
        return
        
    # 执行删除
    cur.execute(f"DELETE FROM papers WHERE id IN ({','.join('?' for _ in outlier_ids)})", outlier_ids)
    conn.commit()
    print(f"[+] Deleted {len(outlier_ids)} rows from DB.")
    conn.close()
    
    # 2. 同步删除 JSON 中的数据
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    papers = [p for p in papers if p['id'] not in outlier_ids]
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
        
    print(f"[+] Synced papers_clean.json. New count: {len(papers)}")
    
if __name__ == '__main__':
    main()