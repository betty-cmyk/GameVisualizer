import sqlite3
from pathlib import Path

DB_PATH = Path('data/papers.db')

if not DB_PATH.exists():
    print("[!] papers.db 不存在")
else:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM papers WHERE db_source LIKE '%GoogleScholar%'")
    new_papers = cur.fetchall()
    
    print(f"\n[*] 游戏文献库新抓取总数: {len(new_papers)} 篇")
    print("=" * 60)
    
    for r in new_papers[:5]:
        p = dict(r)
        print(f"  - 标题: {p.get('title', '')[:50]}")
        print(f"    年份: {p.get('year', '')} | 分类: {p.get('category_9', '')} | 学术层级: {p.get('tier', 'C')}级 | 被引量: {p.get('citations', 0)}次")
        abs_txt = str(p.get('abstract', '') or '').replace('\n', ' ')
        print(f"    摘要: {abs_txt[:60]}..." if len(abs_txt) > 0 else "    摘要: [空]")
        print(f"    链接: {p.get('source_url', '')[:60]}...\n")
    
    print("=" * 60)
    conn.close()
