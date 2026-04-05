import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 恢复按钮 UI 的显示与隐藏逻辑
html = html.replace('document.getElementById(\'d-meta-box\').style.display = \'block\';', "document.getElementById('d-edge-mode-box').style.display = 'flex';\n  document.getElementById('d-meta-box').style.display = 'block';")
html = html.replace("document.getElementById('d-meta-box').style.display = 'none';", "document.getElementById('d-edge-mode-box').style.display = 'none';\n  document.getElementById('d-meta-box').style.display = 'none';")

# 2. 将按钮盒子插入到 HTML 中的正确位置
box_old = """      <div class="detail-title-en" id="d-title-en" style="color:#6e7681;">星图中心计算中...</div>
      
      
      <div class="detail-meta-box" id="d-meta-box" style="display:none;">"""
box_new = """      <div class="detail-title-en" id="d-title-en" style="color:#6e7681;">星图中心计算中...</div>
      
      <div class="edge-mode-switch" id="d-edge-mode-box" style="display:none;">
        <div class="edge-mode-btn active sim" id="btn-sim" onclick="setEdgeMode('sim')">🌌 语义相似网络</div>
        <div class="edge-mode-btn cite" id="btn-cite" onclick="setEdgeMode('cite')">🔗 真实学术引用</div>
      </div>
      
      <div class="detail-meta-box" id="d-meta-box" style="display:none;">"""
html = html.replace(box_old, box_new)

# 3. 恢复画布中选线逻辑：根据 activeEdgeMode 挑选 activeEdges
logic_old = """  let activeSimEdges = [];
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
logic_new = """  let activeEdges = [];
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
html = html.replace(logic_old, logic_new)

# 4. 恢复 Canvas 的分条件绘制
render_old = r"  if \(selectedNode\) \{.*?      \}\n  \}"

render_new = """  if (activeEdges.length > 0) {
      if (activeEdgeMode === 'sim') {
          ctx.beginPath();
          ctx.strokeStyle = "rgba(88, 166, 255, 0.95)";
          ctx.lineWidth = 1.0 / transform.k;
          activeEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
          ctx.stroke();
      } else {
          activeEdges.forEach(e => {
              if (e.target.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.2 / transform.k);
              } 
              else if (e.source.id === selectedNode.id) {
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.2 / transform.k);
              }
          });
      }
  }"""
html = re.sub(render_old, render_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Edges toggle logic restored successfully!")
