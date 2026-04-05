# -*- coding: utf-8 -*-
import os, json, re
from collections import defaultdict
from itertools import combinations

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CRAWLER_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'papers.db')
OUT_JSON = os.path.join(DATA_DIR, 'graph_v3.json')

CATEGORIES = {
    'Game AI': {'label': '游戏人工智能', 'color': '#ff7b72'}, 
    'PCG': {'label': '程序化内容生成', 'color': '#ffa657'}, 
    'Rendering': {'label': '实时渲染与图形', 'color': '#79c0ff'}, 
    'Animation': {'label': '动画与运动合成', 'color': '#56d364'}, 
    'Simulation & Physics': {'label': '物理仿真与碰撞', 'color': '#d2a8ff'}, 
    'HCI/UX in Games': {'label': '人机交互与体验', 'color': '#e3b341'}, 
    'Networking & Systems': {'label': '网络同步与系统', 'color': '#76e3ea'}, 
    'Game Analytics': {'label': '游戏分析与运筹', 'color': '#89d4f5'},
}

def jaccard_sim(a, b):
    if not a or not b: return 0.0
    inter = len(a & b)
    return inter / len(a | b) if len(a | b) > 0 else 0.0

def main():
    import sqlite3
    if not os.path.exists(DB_PATH): return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM papers")
    raw_papers = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    papers = []
    outlier_count = 0
    for p in raw_papers:
        tier = p.get('tier', '')
        cites = p.get('citations', 0)
        # 【全局免疫法则】：剔除跨界毒瘤（如地震学射线追踪等旧时代高引噪声）
        if tier not in ('S', 'A') and cites > 150:
            outlier_count += 1
            continue
        papers.append(p)
    print(f"[!] 过滤筛选机制启动：已自动拦截 {outlier_count} 篇跨界畸高引毒瘤。")

    nodes = []
    edges = []
    idx = 0
    cat_node_id = {}
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
        cats = [p.get('category_9', 'Game AI')]
        if cats[0] not in CATEGORIES: cats[0] = 'Game AI'
        primary = cats[0]
        pid = idx

        words = re.findall(r'[a-zA-Z]{3,}|[\u4e00-\u9fa5]{2,}', title + " " + (p.get('abstract','') or ''))
        token_set = set(w.lower() for w in words if len(w)>2)

        node = {
            'id': pid,
            'label': (title[:20] + '...') if len(title) > 20 else title,
            'full_title': title,
            'title_zh': p.get('title_zh', ''),
            'type': 'paper',
            'color': CATEGORIES[primary]['color'],
            'count': 1, 'r': 4,
            'primary_category': primary,
            'categories': cats,
            'year': p.get('year', ''),
            'author': p.get('author', ''),
            'source_url': p.get('source_url', ''),
            'abstract': p.get('abstract', ''),
            'citations': p.get('citations', 0),
            'tier': p.get('tier', 'C'),
            'openalex_id': p.get('openalex_id', ''),
            'references_list': p.get('references_list', '[]'),
            '_tokens': token_set,
        }
        nodes.append(node)
        paper_nodes.append(node)
        idx += 1

        for c_id in cats:
            c_idx = cat_node_id[c_id]
            nodes[c_idx]['count'] += 1
            nodes[c_idx]['papers'].append({'title': title, 'year': p.get('year', '')})

    paper_sim_list = []
    for i in range(len(paper_nodes)):
        ni = paper_nodes[i]
        ti = ni['_tokens']
        potential_edges = []
        for j in range(i + 1, len(paper_nodes)):
            nj = paper_nodes[j]
            sim = jaccard_sim(ti, nj['_tokens'])
            if sim > 0.05: # 放宽一点点相似度，防止孤星太多
                potential_edges.append({'source': ni['id'], 'target': nj['id'], 'weight': sim * 5, 'type': 'paper_sim', 'val': sim})
        
        potential_edges.sort(key=lambda x: x['val'], reverse=True)
        
        # 【核心修正】：即使相似度不够高，只要不是0，也强制保留最强的 2 条线兜底！
        if potential_edges:
            paper_sim_list.extend(potential_edges[:5])

    edges.extend(paper_sim_list)

    oa_to_pid = {}
    for n in paper_nodes:
        oa_id = str(n.get('openalex_id', '')).split('/')[-1] 
        if oa_id and oa_id != 'NOT_FOUND':
            oa_to_pid[oa_id] = n['id']
            
    citation_edges_count = 0
    for n in paper_nodes:
        ref_str = n.get('references_list', '[]')
        if not ref_str: continue
        try:
            refs = json.loads(ref_str)
            for ref_oa_id in refs:
                target_pid = oa_to_pid.get(ref_oa_id)
                if target_pid:
                    edges.append({'source': n['id'], 'target': target_pid, 'weight': 1, 'type': 'paper_citation'})
                    citation_edges_count += 1
        except:
            pass
            
    print(f"[!] 本地知识图谱内发现真实交叉引用边 (Citation Edges): {citation_edges_count} 条")

    for n in nodes:
        if '_tokens' in n: del n['_tokens']

    graph = {'nodes': nodes, 'edges': edges, 'total': len(papers)}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")

if __name__ == '__main__': main()