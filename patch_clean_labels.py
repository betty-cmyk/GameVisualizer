import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_logic = r"let activeEdges = \[\];\s*let relatedNodes = new Set\(\);\s*if \(selectedNode\) \{.*?\}\n\s*ctx\.save\(\);\s*ctx\.translate"

new_logic = """let activeEdges = [];
    let relatedNodes = new Set();
    if (selectedNode) {
        relatedNodes.add(selectedNode.id);
        
        // 【精准关联】：如果处于相似网络模式，就只收集相似的邻居；如果处于引用模式，就只收集引用的邻居
        const edgePool = (activeEdgeMode === 'sim') ? simEdges : citeEdges;
        edgePool.forEach(e => {
            if (e.source.id === selectedNode.id || e.target.id === selectedNode.id) {
                activeEdges.push(e);
                relatedNodes.add(e.source.id); 
                relatedNodes.add(e.target.id);
            }
        });
    }

    ctx.save();
    ctx.translate"""

html = re.sub(old_logic, new_logic, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Label clutter eliminated!")
