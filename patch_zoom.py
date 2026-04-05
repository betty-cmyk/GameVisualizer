import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 修改初始视野包围盒的放大倍数（从 3.5 倍拉到 5.5 倍），以获得极佳的宏观宇宙感
zoom_old = r'let w = Math\.max\(maxX-minX, 200\) \* 3\.5, h = Math\.max\(maxY-minY, 200\) \* 3\.5;\s*let scale = Math\.max\(0\.1, Math\.min\(2\.0, Math\.min\(width/w, height/h\)\)\);'

zoom_new = """let w = Math.max(maxX-minX, 250) * 5.5, h = Math.max(maxY-minY, 250) * 5.5;
                        let scale = Math.max(0.05, Math.min(1.2, Math.min(width/w, height/h)));"""

html = re.sub(zoom_old, zoom_new, html, flags=re.DOTALL)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Zoom patched!")