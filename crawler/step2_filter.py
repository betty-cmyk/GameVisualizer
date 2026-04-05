# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP_JSON = ROOT / "data" / "temp_raw_cited.json"
FILTERED_JSON = ROOT / "data" / "temp_filtered_cited.json"

def main():
    if not TEMP_JSON.exists():
        print("Error: temp_raw_cited.json 不存在！请先运行 step1_crawl.py")
        return

    raw_papers = json.loads(TEMP_JSON.read_text(encoding='utf-8'))
    print(f"\n=== Step 2: 启动深空毒瘤过滤机 (待处理 {len(raw_papers)} 篇野生文献) ===")
    
    clean_papers = []
    outliers = 0
    
    for p in raw_papers:
        cites = p.get('citations', 0)
        # 【毒瘤拦截网】：抛弃 0 引用的废料，且拦截那些动辄几百上千被引（绝不可能是刚刚派生出的正常游戏前沿论文）的跨界巨怪
        if cites < 1 or cites > 250:
            outliers += 1
            continue
            
        # 它们引用了顶级枢纽，那它自己大概率属于中坚/普通层级
        w_tier = 'B' if cites > 35 else 'C'
        p['tier'] = w_tier
        clean_papers.append(p)
        
    print(f"[!] 已拦截 {outliers} 篇低质量废料或跨界畸高引毒瘤！")
    FILTERED_JSON.write_text(json.dumps(clean_papers, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[OK] Step 2 结束！成功提炼 {len(clean_papers)} 颗纯净的暗物质卫星，暂存至 {FILTERED_JSON.name}。")

if __name__ == '__main__':
    main()
