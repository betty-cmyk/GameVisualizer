import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 精准定位从光环画完之后，到画节点的代码（也就是出错的整片连线区）
pattern = r'ctx\.globalCompositeOperation = "source-over";\s*ctx\.restore\(\);.*?// 鍙戞櫙搴︼紙Alpha锛夊悓鏍烽伒寰瘎绾х涓€闃剁骇娉曞垯'

# 替换为一个极其干净、单层变换、性能极佳的正确画线与点的方法
clean_render = """ctx.globalCompositeOperation = "source-over";
    ctx.restore();
    
    // 【终极重构】：只开启唯一的一个矩阵图层，画网、画红线、画节点，全部在这个完美的同级坐标系内完成！
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);
    
    // 1. 满天星辰背景引力网（性能抢救：只在宏观以上画，极微距太耗能则可适当关闭，当前全画）
    if (transform.k > 0.1 && !selectedNode) { // 优化：太小且没有选中时不画
        ctx.beginPath();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
        ctx.lineWidth = 0.6 / transform.k;
        simEdges.forEach(e => { ctx.moveTo(e.source.x, e.source.y); ctx.lineTo(e.target.x, e.target.y); });
        ctx.stroke();
    }

    let activeEdges = [];
    let relatedNodes = new Set();
    if (selectedNode) {
        relatedNodes.add(selectedNode.id);
        // 用相似网照亮具有相似红蓝色的同类论文光晕
        simEdges.forEach(e => {
            if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
                relatedNodes.add(e.source.id); 
                relatedNodes.add(e.target.id);
            }
        });
        // 根据按钮状态画出连线
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
                if (e.target.id === selectedNode.id) {
                    drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(248, 81, 73, 0.9)", 1.5 / transform.k);
                } else if (e.source.id === selectedNode.id) {
                    drawArrowLine(ctx, e.source.x, e.source.y, e.target.x, e.target.y, "rgba(210, 168, 255, 0.9)", 1.5 / transform.k);
                }
            });
        }
    }

    nodes.forEach(n => {
        // 发光度（Alpha）同样遵循评级第一阶级法则"""

# 把这段极其干净的代码塞进去
html = re.sub(pattern, clean_render, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Canvas rendering pipeline strictly purified!")
