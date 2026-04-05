import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 精确定位 `ctx.globalCompositeOperation = "source-over";` 到 `nodes.forEach(n => {` 之间的全段
render_old = r'ctx\.globalCompositeOperation = "source-over";\s*ctx\.restore\(\);.*?nodes\.forEach\(n => \{'

render_new = """ctx.globalCompositeOperation = "source-over";
  ctx.restore();

  // 【灵魂恢复】：必须先画背景引力网（满天星辰），否则整个宇宙连不成藤蔓
  ctx.save();
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.k, transform.k);
  ctx.beginPath();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.03)"; 
  ctx.lineWidth = 0.6 / transform.k;
  simEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
  ctx.stroke();

  let activeEdges = [];
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
  }

  if (activeEdges.length > 0) {
      if (activeEdgeMode === 'sim') {
          ctx.beginPath();
          ctx.strokeStyle = "rgba(88, 166, 255, 0.95)";
          ctx.lineWidth = 1.0 / transform.k;
          activeEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
          ctx.stroke();
      } else {
          activeEdges.forEach(e => {
              // 红/紫学术射线：极其清晰的方向感
              if (e.target.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.2 / transform.k);
              } 
              else if (e.source.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.2 / transform.k);
              }
          });
      }
  }

  nodes.forEach(n => {"""

html = re.sub(render_old, render_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Edges rendering logic perfected!")
