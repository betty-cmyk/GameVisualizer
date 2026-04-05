import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 极其暴力地斩断“灵魂补回”的那段重复画 12000 条线的垃圾代码！
dupe_old = r'    ctx\.save\(\);\s*ctx\.translate\(transform\.x, transform\.y\);\s*ctx\.scale\(transform\.k, transform\.k\);\s*// 【灵魂补回】：绘制满天星辰的背景引力网（淡弱的语义相似线）\s*ctx\.beginPath\(\);\s*ctx\.strokeStyle = "rgba\(255, 255, 255, 0\.03\)"; \s*ctx\.lineWidth = 0\.6 / transform\.k;\s*simEdges\.forEach\(e => \{ ctx\.moveTo\(e\.source\.x, e\.source\.y\); ctx\.lineTo\(e\.target\.x, e\.target\.y\); \}\);\s*ctx\.stroke\(\);'

html = re.sub(dupe_old, "    ctx.save();\n    ctx.translate(transform.x, transform.y);\n    ctx.scale(transform.k, transform.k);", html, flags=re.DOTALL)

# 2. 控制高斯阴影性能：仅在 transform.k > 0.5 且限制最大模糊半径时开启！
shadow_old = """        if ((selectedNode && relatedNodes.has(n.id))) {
            ctx.shadowColor = n.color;
            ctx.shadowBlur = 18 / transform.k;
            ctx.fill();
            ctx.shadowBlur = 0;
        }"""
shadow_new = """        if ((selectedNode && relatedNodes.has(n.id))) {
            if (transform.k > 0.5) {
                ctx.shadowColor = n.color;
                ctx.shadowBlur = Math.min(18 / transform.k, 30);
                ctx.fill();
                ctx.shadowBlur = 0;
            }
        }"""
html = html.replace(shadow_old, shadow_new)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Render pipeline cleaned and optimized!")
