import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 宏观宇宙半径扩张 (350px -> 650px)
html = html.replace("const radius = 350 * radVariations[i % radVariations.length];", 
                    "const radius = 650 * radVariations[i % radVariations.length];")

# 2. 背景光晕尺寸适配 (350 -> 600)
html = html.replace("const auraRadius = 350 + own.length * 2.5;",
                    "const auraRadius = 600 + own.length * 2.5;")

# 3. 物理学斥力核爆与跑道彻底放宽
force_old = r'\.force\("charge", d3\.forceManyBody\(\)\.strength\(-150\)\.distanceMax\(800\)\)\s*\.force\("center", d3\.forceCenter\(width / 2, height / 2\)\)\s*\.force\("collision", d3\.forceCollide\(\)\.radius\(d => d\.collideR\)\.iterations\(3\)\)\s*\.force\("x", d3\.forceX\(d => \{\s*const cat = catCenters\[d\.primary_category\];\s*if\(!cat\) return width/2;\s*let citeRatio = Math\.min\(\(d\.citations \|\| 0\) / maxCites, 1\.0\);\s*let dustFactor = 1\.0 - Math\.pow\(citeRatio, 0\.3\);.*?let angleOffset = dustFactor \* 2\.5 \+ \(\(d\.id \* 137\) % 100 / 100 - 0\.5\) \* 0\.6;\s*let rOffset = dustFactor \* 200 \+ \(\(d\.id \* 93\) % 100 / 100 - 0\.5\) \* 80;\s*return width/2 \+ Math\.cos\(cat\.baseAngle \+ angleOffset\) \* \(cat\.baseR \+ rOffset\);\s*\}\)\.strength\(0\.07\)\)\s*\.force\("y", d3\.forceY\(d => \{\s*const cat = catCenters\[d\.primary_category\];\s*if\(!cat\) return height/2;\s*let citeRatio = Math\.min\(\(d\.citations \|\| 0\) / maxCites, 1\.0\);\s*let dustFactor = 1\.0 - Math\.pow\(citeRatio, 0\.3\);\s*let angleOffset = dustFactor \* 2\.5 \+ \(\(d\.id \* 137\) % 100 / 100 - 0\.5\) \* 0\.6;\s*let rOffset = dustFactor \* 200 \+ \(\(d\.id \* 93\) % 100 / 100 - 0\.5\) \* 80;\s*return height/2 \+ Math\.sin\(cat\.baseAngle \+ angleOffset\) \* \(cat\.baseR \+ rOffset\);\s*\}\)\.strength\(0\.07\)\)'

force_new = """\.force("charge", d3.forceManyBody().strength(-350).distanceMax(2000))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.collideR).iterations(3))
  .force("x", d3.forceX(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return width/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      let dustFactor = 1.0 - Math.pow(citeRatio, 0.3);
      
      // 【宇宙大撕裂】：超广抛洒角（达 3.5 弧度），超远离心距离（达 400px）！给 3000 个节点极度宽广的存活走廊
      let angleOffset = dustFactor * 3.5 + ((d.id * 137) % 100 / 100 - 0.5) * 0.8;
      let rOffset = dustFactor * 400 + ((d.id * 93) % 100 / 100 - 0.5) * 120;
      return width/2 + Math.cos(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.045)) // 极温柔的向心力，绝生死命往细线上按，让它们依靠斥力蓬松展开
  .force("y", d3.forceY(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return height/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      let dustFactor = 1.0 - Math.pow(citeRatio, 0.3);
      let angleOffset = dustFactor * 3.5 + ((d.id * 137) % 100 / 100 - 0.5) * 0.8;
      let rOffset = dustFactor * 400 + ((d.id * 93) % 100 / 100 - 0.5) * 120;
      return height/2 + Math.sin(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.045))"""

html = re.sub(force_old, force_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Universal expansion layout injected!")
