# -*- coding: utf-8 -*-
import os, json, re
from collections import defaultdict
from itertools import combinations

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CRAWLER_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'papers.db')
OUT_JSON = os.path.join(DATA_DIR, 'graph_v3.json')

# === 游戏科学 8 大核心领域 ===
CATEGORIES = {
    'Game AI': {'label': '游戏人工智能', 'color': '#ff7b72'}, # 红
    'PCG': {'label': '程序化内容生成', 'color': '#ffa657'}, # 橙
    'Rendering': {'label': '实时渲染与图形', 'color': '#79c0ff'}, # 蓝
    'Animation': {'label': '动画与运动合成', 'color': '#56d364'}, # 绿
    'Simulation & Physics': {'label': '物理仿真与碰撞', 'color': '#d2a8ff'}, # 紫
    'HCI/UX in Games': {'label': '人机交互与体验', 'color': '#e3b341'}, # 黄
    'Networking & Systems': {'label': '网络同步与系统', 'color': '#76e3ea'}, # 青
    'Game Analytics': {'label': '游戏分析与运筹', 'color': '#89d4f5'}, # 浅蓝
}

def jaccard_sim(a, b):
    if not a or not b: return 0.0
    inter = len(a & b)
    return inter / len(a | b) if len(a | b) > 0 else 0.0

def main():
    import sqlite3
    if not os.path.exists(DB_PATH): 
        print("Database not found!")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM papers")
    papers = [dict(r) for r in cur.fetchall()]
    conn.close()

    nodes = []
    edges = []
    idx = 0
    cat_node_id = {}
    cat_links = defaultdict(int)
    paper_nodes = []

    for cat_id, cat_info in CATEGORIES.items():
        cat_node_id[cat_id] = idx
        nodes.append({
            'id': idx, 'cat_id': cat_id, 'label': cat_info['label'],
            'type': 'category', 'color': cat_info['color'],
            'count': 0, 'r': 10, 'papers': []
        })
        idx += 1

    for p in papers:
        title = p.get('title', '')
        cats = [p.get('category_9', 'Game AI')] # 默认读库里打好的标
        if cats[0] not in CATEGORIES: cats[0] = 'Game AI'
        primary = cats[0]
        pid = idx

        # 简易分词用于连线
        words = re.findall(r'[a-zA-Z]{3,}|[\u4e00-\u9fa5]{2,}', title + " " + (p.get('abstract','') or ''))
        token_set = set(w.lower() for w in words if len(w)>2)

        node = {
            'id': pid,
            'label': (title[:20] + '...') if len(title) > 20 else title,
            'full_title': title,
            'type': 'paper',
            'color': CATEGORIES[primary]['color'],
            'count': 1, 'r': 4,
            'primary_category': primary,
            'categories': cats,
            'year': p.get('year', ''),
            'author': p.get('author', ''),
            'source_url': p.get('source_url', ''),
            'abstract': p.get('abstract', ''),
            'outline': p.get('outline', ''),
            '_tokens': token_set,
        }
        nodes.append(node)
        paper_nodes.append(node)
        idx += 1

        for c_id in cats:
            c_idx = cat_node_id[c_id]
            nodes[c_idx]['count'] += 1
            nodes[c_idx]['papers'].append({'title': title, 'year': p.get('year', '')})
            edges.append({'source': pid, 'target': c_idx, 'weight': 1, 'type': 'paper_cat'})

    # 论文之间关联
    paper_to_neighbors = defaultdict(list)
    for i in range(len(paper_nodes)):
        ni = paper_nodes[i]
        ti = ni['_tokens']
        for j in range(i + 1, len(paper_nodes)):
            nj = paper_nodes[j]
            sim = jaccard_sim(ti, nj['_tokens'])
            if sim > 0.08:
                edges.append({'source': ni['id'], 'target': nj['id'], 'weight': sim * 5, 'type': 'paper_sim'})

    for n in nodes:
        if '_tokens' in n: del n['_tokens']

    graph = {'nodes': nodes, 'edges': edges, 'total': len(papers)}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")

if __name__ == '__main__': main()