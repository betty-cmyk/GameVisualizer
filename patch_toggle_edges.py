import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 修改相关节点的收集逻辑（无论选择引用还是相似，都用 simEdges 照亮相关节点，但用 edgePool 决定画什么线）
logic_old = """  let activeEdges = [];
  let relatedNodes = new Set();
  if (selectedNode) {
      relatedNodes.add(selectedNode.id);
      const edgePool = (activeEdgeMode === 'sim') ? simEdges : citeEdges;
      edgePool.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              activeEdges.push(e);
              relatedNodes.add(e.source.id); 
              relatedNodes.add(e.target.id);
          }
      });
  }"""

logic_new = """  // 【灵魂补回】：绘制满天星辰的背景引力网（淡弱的语义相似线）
  ctx.beginPath();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
  ctx.lineWidth = 0.6 / transform.k;
  simEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
  ctx.stroke();

  let activeEdges = [];
  let relatedNodes = new Set();
  if (selectedNode) {
      relatedNodes.add(selectedNode.id);
      // 永远通过 sim 照亮具有相似红蓝色的同类论文光晕
      simEdges.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              relatedNodes.add(e.source.id); 
              relatedNodes.add(e.target.id);
          }
      });
      // 但是根据用户点击右侧面板的按钮，决定画出蓝线还是红紫色的学术引用射线！
      const edgePool = (activeEdgeMode === 'sim') ? simEdges : citeEdges;
      edgePool.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              activeEdges.push(e);
              // 如果在引用模式下，也要把有引用关系的论文照亮
              if (activeEdgeMode === 'cite') {
                  relatedNodes.add(e.source.id); 
                  relatedNodes.add(e.target.id);
              }
          }
      });
  }"""
html = html.replace(logic_old, logic_new)

# 2. 优化引用箭头的渲染
render_old = r'if \(activeEdges\.length > 0\) \{.*?\}\n  \}'
render_new = """if (activeEdges.length > 0) {
      if (activeEdgeMode === 'sim') {
          ctx.beginPath();
          ctx.strokeStyle = "rgba(88, 166, 255, 0.95)";
          ctx.lineWidth = 1.0 / transform.k;
          activeEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
          ctx.stroke();
      } else {
          activeEdges.forEach(e => {
              if (e.target.id === selectedNode.id) {
                  // 红色：被选中节点被别人引用（它影响了别人）
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.5 / transform.k);
              } 
              else if (e.source.id === selectedNode.id) {
                  // 紫色：选中节点引用了别人（它站在巨人的肩膀上）
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.5 / transform.k);
              }
          });
      }
  }"""
html = re.sub(render_old, render_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Edges toggle restored with full background web!")
