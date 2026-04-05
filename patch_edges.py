import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 移除多余的边模式切换按钮，保持界面极简
html = re.sub(r'<div class="edge-mode-switch" id="d-edge-mode-box".*?</div>', '', html, flags=re.DOTALL)
html = html.replace("document.getElementById('d-edge-mode-box').style.display = 'flex';", "")
html = html.replace("document.getElementById('d-edge-mode-box').style.display = 'none';", "")

# 2. 收集选中节点的同时，抓取它的语义边和真实的引用边
old_active = """  let activeEdges = [];
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

new_active = """  let activeSimEdges = [];
  let activeCiteEdges = [];
  let relatedNodes = new Set();
  if (selectedNode) {
      relatedNodes.add(selectedNode.id);
      simEdges.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              activeSimEdges.push(e);
              relatedNodes.add(e.source.id);
              relatedNodes.add(e.target.id);
          }
      });
      citeEdges.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              activeCiteEdges.push(e);
              relatedNodes.add(e.source.id);
              relatedNodes.add(e.target.id);
          }
      });
  }"""
html = html.replace(old_active, new_active)

# 3. 渲染法则：全局格局绝对不变，但选中的节点将同时展示其淡蓝语义网和强烈的红紫引用箭头
old_draw = """  if (activeEdges.length > 0) {
      if (activeEdgeMode === 'sim') {
          ctx.beginPath();
          ctx.strokeStyle = "rgba(88, 166, 255, 0.95)";
          ctx.lineWidth = 1.0 / transform.k; // 连线改细
          activeEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
          ctx.stroke();
      } else {
          activeEdges.forEach(e => {
              if (e.target.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 0.8 / transform.k); // 连线改细
              } 
              else if (e.source.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 0.8 / transform.k); // 连线改细
              }
          });
      }
  }"""

new_draw = """  if (selectedNode) {
      if (activeSimEdges.length > 0) {
          ctx.beginPath();
          ctx.strokeStyle = "rgba(88, 166, 255, 0.4)"; // 半透明蓝色，为引用红线让出核心视觉层级
          ctx.lineWidth = 1.0 / transform.k;
          activeSimEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
          ctx.stroke();
      }
      if (activeCiteEdges.length > 0) {
          activeCiteEdges.forEach(e => {
              if (e.target.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.2 / transform.k);
              } 
              else if (e.source.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.2 / transform.k);
              }
          });
      }
  }"""
html = html.replace(old_draw, new_draw)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Citation Edges and UI updated successfully!")
