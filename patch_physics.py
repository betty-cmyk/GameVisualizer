import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

force_old = r'\.force\("link", d3\.forceLink\(allEdges\).*?\.stop\(\);'
force_new = """\.force("link", d3.forceLink(allEdges).id(d => d.id).distance(100).strength(0.01)) // 极弱连线
  .force("charge", d3.forceManyBody().strength(-20).distanceMax(400)) // 彻底粉碎球状斥力，降低为极弱的-20
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.collideR).iterations(3))
  .force("x", d3.forceX(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return width/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      // 【极致星轨】：极其宽松的抛洒跑道（1.8弧度），以及极其舒展的厚度（180px）
      let angleOffset = ((d.id * 137) % 100 / 50 - 1) * (1.0 - Math.pow(citeRatio, 0.4)) * 1.8;
      let rOffset = ((d.id * 93) % 100 / 50 - 1) * (1.0 - citeRatio) * 180;
      return width/2 + Math.cos(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.045)) // 极弱向心力
  .force("y", d3.forceY(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return height/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      let angleOffset = ((d.id * 137) % 100 / 50 - 1) * (1.0 - Math.pow(citeRatio, 0.4)) * 1.8;
      let rOffset = ((d.id * 93) % 100 / 50 - 1) * (1.0 - citeRatio) * 180;
      return height/2 + Math.sin(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.045))
  .stop();"""

html = re.sub(force_old, force_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Physics patched!")
