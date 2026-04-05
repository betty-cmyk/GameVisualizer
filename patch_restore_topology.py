import os

with open('graph_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 恢复 catCenters 到椭圆偏心、不规则的星系分布
start_idx = content.find("const catCenters = {};")
end_idx = content.find("const simulation = d3.forceSimulation(nodes)")

new_cat_block = """const catCenters = {};
categories.forEach((c, i) => {
    const angle = (i / categories.length) * Math.PI * 2;
    // 【椭圆偏心分布】：X轴更宽(450)，Y轴更扁(300)，并加入 20% 的不规则错落，彻底打破正圆感
    const fluctuation = 0.2 * Math.sin(i * 1234.5);
    const radiusX = 450 * (1 + fluctuation);
    const radiusY = 300 * (1 + fluctuation);
    catCenters[c.cat_id] = { x: width/2 + Math.cos(angle)*radiusX, y: height/2 + Math.sin(angle)*radiusY };
});

"""

content = content[:start_idx] + new_cat_block + content[end_idx:]

# 2. 恢复原生拓扑引力（让真实的跨界红线拉出自然悬臂）
start_sim = content.find('.force("link", d3.forceLink')
end_sim = content.find('.stop();', start_sim) + 8

new_sim_block = """\.force("link", d3.forceLink(allEdges).id(d => d.id).distance(120).strength(0.06)) // 强大的真实连线牵引，拉出跨界连串悬臂
  .force("charge", d3.forceManyBody().strength(-200).distanceMax(1000)) // 强大的排斥力，狠狠撑开星团，拒绝实心球
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.collideR).iterations(3))
  .force("x", d3.forceX(d => catCenters[d.primary_category] ? catCenters[d.primary_category].x : width/2).strength(0.045)) // 纯粹的向心力，不做人工干预
  .force("y", d3.forceY(d => catCenters[d.primary_category] ? catCenters[d.primary_category].y : height/2).strength(0.045))
  .stop();"""

content = content[:start_sim] + new_sim_block + content[end_sim:]

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Pure Topology Restored!")
