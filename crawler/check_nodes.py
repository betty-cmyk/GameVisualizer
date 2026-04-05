import json

def main():
    with open('../data/graph_v3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    targets = ['PlenOctrees', '多面体视觉外壳', '预先计算的辐射率传输']
    
    nodes = [n for n in data['nodes'] if n.get('type') == 'paper' and any(t in str(n.get('title_zh', '')) for t in targets)]
    
    for n in nodes:
        nid = n['id']
        edges = [e for e in data['edges'] if e['source'] == nid or e['target'] == nid]
        sim_edges = [e for e in edges if e.get('type') == 'paper_sim']
        cite_edges = [e for e in edges if e.get('type') == 'paper_citation']
        
        print(f"ID: {nid}")
        print(f"Title: {n.get('title_zh')} / {n.get('full_title')}")
        print(f"Category: {n.get('primary_category')}")
        print(f"Citations: {n.get('citations')}")
        print(f"Total Edges: {len(edges)} (Sim: {len(sim_edges)}, Cite: {len(cite_edges)})")
        print("-" * 50)

if __name__ == '__main__':
    main()