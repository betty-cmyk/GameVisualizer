# -*- coding: utf-8 -*-
import os

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(CRAWLER_DIR, '..')
DATA_DIR = os.path.join(ROOT, 'data')
DOCS_DIR = os.path.join(ROOT, 'docs')
GRAPH_JSON = os.path.join(DATA_DIR, 'graph_v3.json')
TEMPLATE_FILE = os.path.join(ROOT, 'graph_template.html')
OUT_HTML = os.path.join(DOCS_DIR, 'index.html')

def main():
    if not os.path.exists(GRAPH_JSON):
        print(f"Error: {GRAPH_JSON} not found!")
        return
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: {TEMPLATE_FILE} not found!")
        return

    # 读取图谱数据
    with open(GRAPH_JSON, 'r', encoding='utf-8') as f:
        gdata = f.read()

    # 读取最新的 Canvas 硬件加速模板
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        tpl = f.read()

    # 注入数据
    html = tpl.replace('{GRAPH_DATA}', gdata)

    # 确保 docs 目录存在
    if not os.path.exists(DOCS_DIR): os.makedirs(DOCS_DIR)

    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Successfully built hardware-accelerated site: {OUT_HTML}')

if __name__ == '__main__':
    main()