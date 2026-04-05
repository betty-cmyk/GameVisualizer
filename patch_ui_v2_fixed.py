import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 注入 Search UI 的 CSS
css_old = "      #charts-btn {"
css_new = """  #search-container { position: absolute; top: 20px; left: 380px; z-index: 150; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
  #search-input { width: 350px; background: rgba(13,17,23,0.85); border: 1px solid #1f242e; color: #c9d1d9; padding: 10px 16px; border-radius: 20px; outline: none; backdrop-filter: blur(10px); font-size: 12px; transition: 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
  #search-input:focus { border-color: #58a6ff; box-shadow: 0 0 15px rgba(88,166,255,0.3); width: 400px; }
  #search-results { position: absolute; top: 45px; left: 0; width: 100%; max-height: 350px; overflow-y: auto; background: rgba(13,17,23,0.95); border: 1px solid #1f242e; border-radius: 8px; display: none; backdrop-filter: blur(12px); box-shadow: 0 8px 24px rgba(0,0,0,0.8); }
  #search-results::-webkit-scrollbar { width: 6px; }
  #search-results::-webkit-scrollbar-thumb { background-color: #30363d; border-radius: 3px; }
  .search-item { padding: 10px 15px; border-bottom: 1px solid #1f242e; cursor: pointer; transition: 0.2s; }
  .search-item:last-child { border-bottom: none; }
  .search-item:hover { background: #1f242e; }

  #charts-btn {"""
html = html.replace(css_old, css_new)

# 2. 注入 Search UI 的 HTML
html_old = """  <div id="toggle-labels-btn" title="Toggle Global Labels" onclick="toggleGlobalLabels()">👁️</div>

  <canvas id="main-canvas"></canvas>"""
html_new = """  <div id="toggle-labels-btn" title="Toggle Global Labels" onclick="toggleGlobalLabels()">👁️</div>
  <div id="search-container">
    <input type="text" id="search-input" placeholder="🔍 搜索论文标题、作者... (回车确认)" autocomplete="off" />
    <div id="search-results"></div>
  </div>
  <canvas id="main-canvas"></canvas>"""
html = html.replace(html_old, html_new)

# 3. 彻底重铸力场：极长切向抛洒 + 极度扁平径向压缩
force_old = r'\.force\("link", d3\.forceLink\(allEdges\).*?\.stop\(\);'
force_new = """\.force("link", d3.forceLink(allEdges).id(d => d.id).distance(80).strength(0.015)) // 连线拉力降到极弱，允许彻底拉长
  .force("charge", d3.forceManyBody().strength(-70).distanceMax(400)) // 局部斥力降到极弱，彻底消除“硬皮球”块状感
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(d => d.collideR).iterations(2))
  .force("x", d3.forceX(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return width/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      // 【极致扁长弧形】：偏角飙升到 2.8 弧度(160度)，尾迹极其漫长；离心半径被死死压缩到仅仅 40px，强迫形成细长带状
      let angleOffset = ((d.id * 137) % 100 / 50 - 1) * (1.0 - Math.pow(citeRatio, 0.3)) * 2.8;
      let rOffset = ((d.id * 93) % 100 / 50 - 1) * (1.0 - citeRatio) * 40;
      return width/2 + Math.cos(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.08)) // 增强坐标顺从度，逼迫它们站成一排弧线
  .force("y", d3.forceY(d => {
      const cat = catCenters[d.primary_category];
      if(!cat) return height/2;
      let citeRatio = Math.min((d.citations || 0) / maxCites, 1.0);
      let angleOffset = ((d.id * 137) % 100 / 50 - 1) * (1.0 - Math.pow(citeRatio, 0.3)) * 2.8;
      let rOffset = ((d.id * 93) % 100 / 50 - 1) * (1.0 - citeRatio) * 40;
      return height/2 + Math.sin(cat.baseAngle + angleOffset) * (cat.baseR + rOffset);
  }).strength(0.08))
  .stop();"""
html = re.sub(force_old, force_new, html, flags=re.DOTALL)

# 4. 点击空白处关闭搜索框
click_old = "canvas.addEventListener('click', () => {"
click_new = "canvas.addEventListener('click', () => {\n  document.getElementById('search-results').style.display = 'none';"
html = html.replace(click_old, click_new)

# 5. 【修复版】：精准向主逻辑代码末尾注入，不碰前方的 <script src=...>
search_logic = """
// --- 智能检索引擎模块 ---
document.getElementById('search-input').addEventListener('keydown', e => {
    if(e.key === 'Enter') {
        const q = e.target.value.toLowerCase().trim();
        const resBox = document.getElementById('search-results');
        if(!q) { resBox.style.display = 'none'; return; }
        
        const hits = nodes.filter(n => 
            (n.title_zh && n.title_zh.toLowerCase().includes(q)) ||
            (n.full_title && n.full_title.toLowerCase().includes(q)) ||
            (n.author && n.author.toLowerCase().includes(q))
        ).sort((a,b) => (b.citations||0) - (a.citations||0)).slice(0, 30);
        
        resBox.innerHTML = '';
        if(hits.length === 0) {
            resBox.innerHTML = '<div style="padding:15px;color:#8b949e;font-size:12px;text-align:center;">未找到匹配的文献</div>';
        } else {
            hits.forEach(h => {
                const div = document.createElement('div');
                div.className = 'search-item';
                const titleShow = h.title_zh ? h.title_zh : h.full_title;
                div.innerHTML = `
                    <div style="color:#e6edf3;font-weight:bold;margin-bottom:4px;font-size:12px;line-height:1.4;">${titleShow}</div>
                    <div style="color:#8b949e;font-size:11px;display:flex;justify-content:space-between;">
                        <span>👤 ${h.author ? h.author.split('/')[0] + ' et al.' : '未知'}</span>
                        <span style="color:#58a6ff">🔥 ${h.citations||0}</span>
                    </div>
                `;
                div.onclick = () => {
                    e.target.value = titleShow;
                    resBox.style.display = 'none';
                    focusNode(h.id, true); 
                };
                resBox.appendChild(div);
            });
        }
        resBox.style.display = 'block';
    }
});
</script>
</body>
</html>
"""

html = html.replace("</script>\n</body>\n</html>", search_logic)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Patched V2 Fixed successfully!")
