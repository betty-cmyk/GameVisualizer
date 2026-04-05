import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_logic = r"let topPaper = \[\];.*?let tx = width / 2 - scale \* cx;.*?\n.*?render\(\);"
# 不使用复杂的正则，我直接找 setTimeout 内部的这一大段块

start_idx = html.find("if (nodes.length > 0) {")
end_idx = html.find("initCharts();")

new_logic = """if (nodes.length > 0) {
                    // 【极致特写】：硬降落 NVIDIA RTX，或者寻找中小型连线节点
                    let targetPaper = nodes.find(n => n.title_zh && n.title_zh.includes('NVIDIA 光线追踪'));
                    if (!targetPaper) targetPaper = nodes.find(n => n.full_title && n.full_title.includes('NVIDIA Ray Tracing'));
                    if (!targetPaper) {
                        let renderingNodes = [...nodes].filter(n => n.primary_category === 'Rendering');
                        for (let n of renderingNodes) {
                            let edgeCount = allEdges.filter(e => e.source.id === n.id || e.target.id === n.id).length;
                            if (edgeCount > 0 && edgeCount < 10) {
                                targetPaper = n;
                                break;
                            }
                        }
                    }
                    if (!targetPaper) targetPaper = [...nodes].filter(n => n.primary_category === 'Rendering').sort((a,b) => (b.citations||0) - (a.citations||0))[0] || nodes[0];

                    if (targetPaper) {
                        selectedNode = targetPaper;
                        showDetail(targetPaper);
                        
                        let relNodesSet = new Set();
                        simEdges.forEach(e => { if(e.source.id===targetPaper.id) relNodesSet.add(e.target); else if(e.target.id===targetPaper.id) relNodesSet.add(e.source); });
                        citeEdges.forEach(e => { if(e.source.id===targetPaper.id) relNodesSet.add(e.target); else if(e.target.id===targetPaper.id) relNodesSet.add(e.source); });
                        
                        // 不依赖未收敛的 x/y 距离计算，避免 NaN，直接抓取前 3 个邻居！
                        let neighbors = Array.from(relNodesSet).filter(n => n && n.id !== targetPaper.id);
                        let coreNodes = [targetPaper, ...neighbors.slice(0, 3)];
                        
                        let minX = d3.min(coreNodes, n=>n.x), maxX = d3.max(coreNodes, n=>n.x);
                        let minY = d3.min(coreNodes, n=>n.y), maxY = d3.max(coreNodes, n=>n.y);
                        let cx = (minX + maxX) / 2;
                        let cy = (minY + maxY) / 2;
                        
                        // 极度收紧，不乘外扩系数，只加上少许呼吸 padding，形成电影特写感
                        let w = Math.max(maxX - minX, 60) + 120;
                        let h = Math.max(maxY - minY, 60) + 120;
                        let scale = Math.max(0.8, Math.min(2.5, Math.min(width/w, height/h)));
                        
                        let tx = width / 2 - scale * cx;
                        let ty = height / 2 - scale * cy;
                        
                        d3.select(canvas).transition().duration(2500).ease(d3.easeCubicOut)
                          .call(zoomObj.transform, d3.zoomIdentity.translate(tx, ty).scale(scale))
                          .on('end', () => render());
                        render();
                    }
                }
                """

html = html[:start_idx] + new_logic + html[end_idx:]

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Initial Zoom Patched!")
