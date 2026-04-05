import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 把连线变细
html = html.replace('ctx.lineWidth = 2.5 / transform.k;', 'ctx.lineWidth = 1.0 / transform.k;')
html = html.replace('2.0 / transform.k', '0.8 / transform.k')

# 2. 初始宏观包围盒 (Zoom Out)
zoom_old = """                    if (topPaper) { focusNode(topPaper.id, false); showDetail(topPaper); }"""
zoom_new = """                    if (topPaper) {
                        selectedNode = topPaper;
                        showDetail(topPaper);
                        let rels = new Set([topPaper.id]);
                        simEdges.forEach(e => { if(e.source.id===topPaper.id) rels.add(e.target.id); else if(e.target.id===topPaper.id) rels.add(e.source.id); });
                        citeEdges.forEach(e => { if(e.source.id===topPaper.id) rels.add(e.target.id); else if(e.target.id===topPaper.id) rels.add(e.source.id); });
                        let relNodes = nodes.filter(n => rels.has(n.id));
                        if (relNodes.length === 0) relNodes = [topPaper];
                        let minX = d3.min(relNodes, n=>n.x), maxX = d3.max(relNodes, n=>n.x);
                        let minY = d3.min(relNodes, n=>n.y), maxY = d3.max(relNodes, n=>n.y);
                        let cx = (minX + maxX)/2, cy = (minY + maxY)/2;
                        let w = Math.max(maxX-minX, 200) * 3.5, h = Math.max(maxY-minY, 200) * 3.5;
                        let scale = Math.max(0.1, Math.min(2.0, Math.min(width/w, height/h)));
                        let tx = width/2 - scale*cx, ty = height/2 - scale*cy;
                        d3.select(canvas).transition().duration(2500).ease(d3.easeCubicOut).call(zoomObj.transform, d3.zoomIdentity.translate(tx, ty).scale(scale)).on('end', ()=>render());
                        render();
                    }"""
html = html.replace(zoom_old, zoom_new)

# 3. 智能八方向避让防遮挡
label_old = """  sortedNodes.forEach((n, idx) => {
      const screenX = n.x * transform.k + transform.x;
      const screenY = n.y * transform.k + transform.y;
      if (screenX < -50 || screenX > width + 50 || screenY < -50 || screenY > height + 50) return;
      
      let isFocus = selectedNode && relatedNodes.has(n.id);
      
      // 1. 交互态：只要点击了某个节点，严格【只显示】它和它周围关联节点的名字
      if (selectedNode && !isFocus) return; 
      
      // 2. 全局态：未点击任何节点时，死死卡住全局【只显示前 3 个】超级核心的名字
      if (!selectedNode && !showGlobalLabels && transform.k < 2.5) {
          if (idx >= 3) return;
      }

      const screenR = n.r * transform.k;
      const fontSize = isFocus ? 13 : 11;
      ctx.font = `${isFocus ? 'bold ' : ''}${fontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
      
      let displayName = n.title_zh ? n.title_zh : n.full_title;
      if (!isFocus && displayName.length > 30) {
          displayName = displayName.substring(0, 30) + '...';
      }
      
      const lines = wrapText(ctx, displayName, isFocus ? 250 : 120);
      const lineHeight = fontSize * 1.4;
      const textHeight = lines.length * lineHeight;
      
      const box = {
          left: screenX + screenR + 6,
          right: screenX + screenR + 6 + (isFocus ? 250 : 120),
          top: screenY - textHeight/2,
          bottom: screenY + textHeight/2
      };

      if (!isFocus && showGlobalLabels) {
          let overlap = drawnBoxes.some(b => intersectRect(box, b));
          if (overlap) return;
      }
      drawnBoxes.push(box);

      if (isFocus) {
          ctx.fillStyle = "#ffffff";
      } else if (n.tier === 'S') {
          ctx.fillStyle = "rgba(201, 209, 217, 0.85)";
      } else {
          const textAlpha = Math.max(0, Math.min(1, (transform.k - 2.5) / 1.5));
          ctx.fillStyle = `rgba(139, 148, 158, ${textAlpha * 0.5})`;
      }
      lines.forEach((line, i) => {
          ctx.fillText(line, box.left, box.top + i * lineHeight);
      });
  });"""

label_new = """  sortedNodes.forEach((n, idx) => {
      const screenX = n.x * transform.k + transform.x;
      const screenY = n.y * transform.k + transform.y;
      if (screenX < -50 || screenX > width + 50 || screenY < -50 || screenY > height + 50) return;
      
      let isFocus = selectedNode && relatedNodes.has(n.id);
      if (selectedNode && !isFocus) return; 
      if (!selectedNode && !showGlobalLabels && transform.k < 2.5) { if (idx >= 3) return; }

      const screenR = n.r * transform.k;
      const fontSize = isFocus ? 13 : 11;
      ctx.font = `${isFocus ? 'bold ' : ''}${fontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
      
      let displayName = n.title_zh ? n.title_zh : n.full_title;
      if (!isFocus && displayName.length > 30) displayName = displayName.substring(0, 30) + '...';
      
      const lines = wrapText(ctx, displayName, isFocus ? 250 : 120);
      const textWidth = Math.max(...lines.map(l => ctx.measureText(l).width));
      const lineHeight = fontSize * 1.4;
      const textHeight = lines.length * lineHeight;
      
      let placed = false;
      let bestX = screenX + screenR + 6, bestY = screenY - textHeight/2;
      let finalBox = null;

      // 【核心】：螺旋 8 向试探碰撞算法，无论如何不能让焦点文字叠在一起
      if (isFocus || showGlobalLabels) {
          const angles = [0, Math.PI/4, Math.PI/2, 3*Math.PI/4, Math.PI, -3*Math.PI/4, -Math.PI/2, -Math.PI/4];
          // 搜索3层距离
          for (let step = 0; step < 4 && !placed; step++) {
              let rOffset = screenR + 8 + step * 18;
              for (let a of angles) {
                  let anchorX = screenX + Math.cos(a) * rOffset;
                  let anchorY = screenY + Math.sin(a) * rOffset;
                  // 根据象限调整文字对齐锚点，避免盖住节点
                  let bLeft = (Math.cos(a) > 0.1) ? anchorX : (Math.cos(a) < -0.1 ? anchorX - textWidth : anchorX - textWidth/2);
                  let bTop = (Math.sin(a) > 0.1) ? anchorY : (Math.sin(a) < -0.1 ? anchorY - textHeight : anchorY - textHeight/2);
                  
                  let box = { left: bLeft-4, right: bLeft+textWidth+4, top: bTop-4, bottom: bTop+textHeight+4 };
                  if (!drawnBoxes.some(b => intersectRect(box, b))) {
                      bestX = bLeft; bestY = bTop; finalBox = box; placed = true; break;
                  }
              }
          }
      }
      
      if (!placed) finalBox = { left: bestX-4, right: bestX+textWidth+4, top: bestY-4, bottom: bestY+textHeight+4 };
      if (!isFocus && showGlobalLabels && drawnBoxes.some(b => intersectRect(finalBox, b))) return;
      drawnBoxes.push(finalBox);

      if (isFocus) ctx.fillStyle = "#ffffff";
      else if (n.tier === 'S') ctx.fillStyle = "rgba(201, 209, 217, 0.85)";
      else { const tAlpha = Math.max(0, Math.min(1, (transform.k - 2.5)/1.5)); ctx.fillStyle = `rgba(139,148,158,${tAlpha*0.5})`; }
      
      lines.forEach((line, i) => { ctx.fillText(line, bestX, bestY + i * lineHeight); });
  });"""

html = html.replace(label_old, label_new)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Patched successfully!")