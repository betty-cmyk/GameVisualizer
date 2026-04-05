import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 恢复 D3 拓扑自然力场（真实连线拉出悬臂，而非人工数学公式）
force_old = r'\.force\("link", d3\.forceLink\(allEdges\).*?\.stop\(\);'
force_new = """\.force("link", d3.forceLink(allEdges).id(d => d.id).distance(120).strength(0.05)) // 恢复弹簧拉力，让真实的学术连线拉出“连成串”的自然藤蔓形态
  .force("charge", d3.forceManyBody().strength(-180).distanceMax(1000)) // 恢复强大的斥力，把拥挤的节点狠狠撑开
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.collideR).iterations(3))
  .force("x", d3.forceX(d => catCenters[d.primary_category] ? catCenters[d.primary_category].x : width/2).strength(0.04)) // 极其温柔的向心引力
  .force("y", d3.forceY(d => catCenters[d.primary_category] ? catCenters[d.primary_category].y : height/2).strength(0.04))
  .stop();"""

html = re.sub(force_old, force_new, html, flags=re.DOTALL)

# 2. 增强宇宙轨道错落感（扩大到 15% 浮动，让 8 大分类分布更不规则）
cat_old = r'const fluctuation = 0\.1 \* Math\.sin\(i \* 1234\.5\);'
cat_new = 'const fluctuation = 0.15 * Math.sin(i * 1234.5);'
html = re.sub(cat_old, cat_new, html)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Topology physics restored!")
