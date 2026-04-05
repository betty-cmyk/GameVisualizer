import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 恢复控制面板的 🌌语义 / 🔗引用 按钮，替换到档案栏里面
box_old = """      <div class="detail-title-en" id="d-title-en" style="color:#6e7681;">星图中心计算中...</div>
      
      
      <div class="detail-meta-box" id="d-meta-box" style="display:none;">"""
box_new = """      <div class="detail-title-en" id="d-title-en" style="color:#6e7681;">星图中心计算中...</div>
      
      <div class="edge-mode-switch" id="d-edge-mode-box" style="display:none;">
        <div class="edge-mode-btn active sim" id="btn-sim" onclick="setEdgeMode('sim')">🌌 语义相似网络</div>
        <div class="edge-mode-btn cite" id="btn-cite" onclick="setEdgeMode('cite')">🔗 真实学术引用</div>
      </div>
      
      <div class="detail-meta-box" id="d-meta-box" style="display:none;">"""
html = html.replace(box_old, box_new)

# 2. 修复 JS 显隐控制
html = html.replace("document.getElementById('d-meta-box').style.display = 'block';", "document.getElementById('d-edge-mode-box').style.display = 'flex';\n  document.getElementById('d-meta-box').style.display = 'block';")
html = html.replace("document.getElementById('d-meta-box').style.display = 'none';", "document.getElementById('d-edge-mode-box').style.display = 'none';\n  document.getElementById('d-meta-box').style.display = 'none';")

# 3. 完美处理 activeEdges (只在 selectedNode 下过滤出来，不污染全局)
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
logic_new = """  let activeEdges = [];
  let relatedNodes = new Set();
  if (selectedNode) {
      relatedNodes.add(selectedNode.id);
      // 永远用 simEdges 照亮关联节点的光晕
      simEdges.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              relatedNodes.add(e.source.id); 
              relatedNodes.add(e.target.id);
          }
      });
      // 根据按钮，专门筛选出要画的 高亮连接线 (蓝/红紫)
      const edgePool = (activeEdgeMode === 'sim') ? simEdges : citeEdges;
      edgePool.forEach(e => {
          if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
              activeEdges.push(e);
              if (activeEdgeMode === 'cite') {
                  relatedNodes.add(e.source.id); 
                  relatedNodes.add(e.target.id);
              }
          }
      });
  }"""
html = html.replace(logic_old, logic_new)

# 4. 完美渲染红紫箭头
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
                  // 红色：它被别人引用
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.5 / transform.k);
              } else if (e.source.id === selectedNode.id) {
                  // 紫色：它引用了别人
                  drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.5 / transform.k);
              }
          });
      }
  }"""
html = re.sub(render_old, render_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Citation Toggle feature impeccably injected!")
