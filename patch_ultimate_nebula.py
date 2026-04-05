import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 废除小人椭圆，使用自然不规则星系散布
cat_old = r'const catCenters = \{\};.*?\}\);'
cat_new = """const catCenters = {};
// 【打破小人椭圆】：使用一组人工调优的自然波动系数，产生极其错落、浩瀚的星云群落分布
const radVariations = [1.0, 1.25, 0.85, 1.15, 0.9, 1.3, 0.95, 1.1];
categories.forEach((c, i) => {
    const angle = (i / categories.length) * Math.PI * 2;
    const radius = 350 * radVariations[i % radVariations.length]; 
    catCenters[c.cat_id] = { baseAngle: angle, baseR: radius, x: width/2 + Math.cos(angle)*radius, y: height/2 + Math.sin(angle)*radius };
});"""
html = re.sub(cat_old, cat_new, html, flags=re.DOTALL)

# 2. 注入数学与物理的终极融合引擎（引导长尾弧度 + 物理蓬松厚度）
force_old = r'\.force\("x", d3\.forceX.*?\.stop\(\);'
force_new = """\.force("x", d3.forceX(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return width/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      // 【数学引导长尾】：让尘埃顺着星系轨道拖出长达 1.8 弧度(约100度)的极长尾迹
      let angleOffset = (1.0 - Math.pow(citeRatio, 0.4)) * 1.8;
      return width/2 + Math.cos(cat.baseAngle + angleOffset) * cat.baseR;
  }).strength(0.04)) // 【物理蓬松厚度】：温柔的向心力配合 -180 的强烈斥力，会让原本扁平的跑道炸开成宽阔优美的长悬臂！
  .force("y", d3.forceY(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return height/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      let angleOffset = (1.0 - Math.pow(citeRatio, 0.4)) * 1.8;
      return height/2 + Math.sin(cat.baseAngle + angleOffset) * cat.baseR;
  }).strength(0.04))
  .stop();"""
html = re.sub(force_old, force_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Ultimate Nebula Patched!")
