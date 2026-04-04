# -*- coding: utf-8 -*-
import os, json

CRAWLER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(CRAWLER_DIR, '..')
DATA_DIR = os.path.join(ROOT, 'data')
DOCS_DIR = os.path.join(ROOT, 'docs')
GRAPH_JSON = os.path.join(DATA_DIR, 'graph_v3.json')
OUT_HTML = os.path.join(DOCS_DIR, 'index.html')

HTML_TPL = '''\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>游戏科学与图形学知识图谱</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',sans-serif;overflow:hidden}
#app{width:100vw;height:100vh;display:flex}
#sidebar{width:320px;min-width:320px;background:#161b22;border-right:1px solid #30363d;display:flex;flex-direction:column;transition:width .3s;z-index:100}
#sidebar.collapsed{width:0;min-width:0}
#sb-header{padding:15px;border-bottom:1px solid #30363d;display:flex;justify-content:space-between;align-items:center}
#sb-title{font-size:14px;color:#79c0ff;font-weight:bold}
#sb-toggle{background:none;border:1px solid #30363d;color:#8b949e;border-radius:4px;padding:2px 8px;cursor:pointer}
#sb-list{flex:1;overflow-y:auto;padding:5px}
.sb-item{padding:12px;border-bottom:1px solid #21262d;font-size:12px}
.sb-item-title{color:#e6edf3;margin-bottom:5px;line-height:1.4}
#graph-wrap{flex:1;position:relative;background:radial-gradient(circle at center, #161b22 0%, #0d1117 100%)}
svg{width:100%;height:100%}
#sidebar-right{width:360px;min-width:360px;background:#161b22;border-left:1px solid #30363d;display:flex;flex-direction:column;transition:width .3s;z-index:100;transform:translateX(100%);position:absolute;right:0;top:0;bottom:0}
#sidebar-right.active{transform:translateX(0)}
#sbr-header{padding:15px;border-bottom:1px solid #30363d;display:flex;justify-content:space-between;align-items:center}
#sbr-title{font-size:14px;color:#79c0ff;font-weight:bold}
#sbr-toggle{background:none;border:1px solid #30363d;color:#8b949e;border-radius:4px;padding:2px 8px;cursor:pointer}
#sbr-list{flex:1;overflow-y:auto;padding:15px;font-size:12px;color:#e6edf3;line-height:1.6}
.hull{stroke-width:1.4}
.cat-label{font-size:13px;font-weight:700;paint-order:stroke;stroke:#0d1117;stroke-width:3px;stroke-linejoin:round}
#analysis-btn{position:absolute;top:20px;right:20px;background:#388bfd;color:#fff;border:none;padding:10px 16px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold;pointer-events:auto;box-shadow:0 0 10px rgba(56,139,253,0.4);z-index:150;}
#charts-tray{position:fixed;bottom:-320px;left:0;right:0;height:320px;background:#161b22;border-top:1px solid #30363d;transition:bottom .3s, right .3s;z-index:200;padding:14px;display:flex;gap:12px;overflow-x:auto}
#charts-tray.active{bottom:0}
#charts-tray.with-sbr{right:360px}
.chart-box{min-width:300px;flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:15px;display:flex;flex-direction:column}
.chart-title{font-size:13px;color:#79c0ff;margin-bottom:10px;text-align:center;font-weight:bold}
#close-tray{position:absolute;top:10px;right:10px;background:none;border:none;color:#8b949e;cursor:pointer;font-size:20px}
.stat-tag{display:inline-block;padding:2px 8px;border-radius:12px;font-size:10px;margin:2px;background:#21262d;border:1px solid #30363d}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div id="sb-header"><span id="sb-title">文献库</span><button id="sb-toggle" onclick="toggleSB()">收起</button></div>
    <div id="sb-list"></div>
  </div>
  <div id="graph-wrap">
    <svg id="svg"><g id="root"><g id="gh"></g><g id="ge"></g><g id="gn"></g></g></svg>
    <button id="analysis-btn" onclick="toggleAnalysis()">查看图表统计</button>
    <div id="sidebar-right" class="active">
      <div id="sbr-header"><span id="sbr-title">论文档案</span><button id="sbr-toggle" onclick="toggleSBR()">关闭</button></div>
      <div id="sbr-list">请在网络图中点击具体论文气泡查看详细信息。</div>
    </div>
    <div id="charts-tray">
      <button id="close-tray" onclick="toggleAnalysis()">×</button>
      <div class="chart-box" id="chart-years"><div class="chart-title">历年论文产出趋势</div><div class="chart-canvas" style="flex:1"></div></div>
      <div class="chart-box" id="chart-cats"><div class="chart-title">研究方向分布</div><div class="chart-canvas" style="flex:1"></div></div>
      <div class="chart-box" id="chart-units"><div class="chart-title">高被引论文 Top10</div><div class="chart-canvas" style="flex:1"></div></div>
    </div>
  </div>
</div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const G = {GRAPH_DATA};
let svg, root, sbOpen = true, kScale = 1;

function toggleSB(){
  sbOpen=!sbOpen;
  document.getElementById('sidebar').classList.toggle('collapsed',!sbOpen);
  document.getElementById('sb-toggle').textContent=sbOpen?'收起':'展开';
}

let sbrOpen = true;
function toggleSBR(){
  sbrOpen=!sbrOpen;
  document.getElementById('sidebar-right').classList.toggle('active', sbrOpen);
  document.getElementById('charts-tray').classList.toggle('with-sbr', sbrOpen);
}

function showInfo(d){
  if(d.type === 'category'){
    const list = document.getElementById('sb-list');
    document.getElementById('sb-title').textContent = d.label;
    const papers = (d.papers || []).sort((a,b)=>((b.year||'0')<(a.year||'0')?-1:1));
    list.innerHTML = `<div style="padding:10px;font-size:11px;color:#8b949e;background:#0d1117;margin-bottom:5px">共收集论文 ${papers.length} 篇</div>` + 
      papers.map((p,i)=>`<div class="sb-item" onclick='focusPaper(${JSON.stringify(p.title)})'><div class="sb-item-title">${i+1}. ${p.title}</div><div style="display:flex;justify-content:space-between;color:#8b949e"><span>${p.year||'未知'}</span></div></div>`).join('');
    if(!sbOpen) toggleSB();
  }else{
    const rlist = document.getElementById('sbr-list');
    document.getElementById('sbr-title').textContent = '论文档案';
    rlist.innerHTML = `<div style="font-size:15px;color:#79c0ff;font-weight:bold;margin-bottom:15px;border-bottom:1px solid #30363d;padding-bottom:10px">${d.full_title}</div>
      <div style="display:flex;justify-content:space-between;color:#8b949e;margin-bottom:10px">
        <span>📅 年份：${d.year||'未知'}</span>
        <span>🔥 被引：${d.citations||'0'}</span>
      </div>
      <div style="margin-bottom:10px">
        <span class="stat-tag" style="background:#11331f;border-color:#238636">🏷️ 分类: ${d.primary_category||'Game AI'}</span>
        <span class="stat-tag" style="background:#11331f;border-color:#238636">🎖️ 会议评级: ${d.tier||'C'}</span>
      </div>
      <div style="margin-bottom:20px">
        <a href="${(d.url||d.source_url||('https://scholar.google.com/scholar?q=' + encodeURIComponent(d.full_title||'')))}" target="_blank" style="display:inline-block;background:#238636;color:#ffffff;padding:6px 12px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:bold;">🔍 打开学术文献详情页</a>
      </div>
      <div style="color:#e6edf3;margin-bottom:15px"><strong>作者：</strong>${d.author||'未记录'}</div>
      <div style="color:#79c0ff;margin-bottom:8px;font-weight:bold">核心摘要</div>
      <div style="background:#0d1117;padding:12px;border-radius:6px;border:1px solid #30363d;margin-bottom:20px;text-align:justify;">${d.abstract||'暂无摘要信息，请点击上方链接查看全文。'}</div>
    `;
    if(!sbrOpen) toggleSBR();
  }
}

function focusPaper(title){
  const p = G.nodes.find(n=>n.full_title === title);
  if(p) showInfo(p);
}

let chartsInited = false;
function toggleAnalysis(){
  const tray = document.getElementById('charts-tray');
  tray.classList.toggle('active');
  if(tray.classList.contains('active') && !chartsInited) {
    initCharts();
    chartsInited = true;
  }
}

function initCharts(){
  // 简单模拟图表初始化（仅供占位，如果要用ECharts需要引入CDN）
  document.getElementById('chart-years').innerHTML += '<div style="color:#8b949e;text-align:center;margin-top:50px">图表已加载 (使用 d3 渲染或后续接入 eCharts)</div>';
  document.getElementById('chart-cats').innerHTML += '<div style="color:#8b949e;text-align:center;margin-top:50px">图表已加载</div>';
  document.getElementById('chart-units').innerHTML += '<div style="color:#8b949e;text-align:center;margin-top:50px">图表已加载</div>';
}

function render(){
  const W = document.getElementById('graph-wrap').clientWidth;
  const H = window.innerHeight;

  const categories = G.nodes.filter(n=>n.type==='category');
  const papers = G.nodes.filter(n=>n.type==='paper');
  const catByKey = new Map(categories.map(c=>[c.cat_id,c]));

  const S = 50;

  categories.forEach((c, i)=>{
    c.x = W/2 + Math.cos(i/categories.length * Math.PI * 2) * S * 4;
    c.y = H/2 + Math.sin(i/categories.length * Math.PI * 2) * S * 4;
  });

  papers.forEach(p => {
    const pc = catByKey.get(p.primary_category);
    if (pc) {
       p.x = pc.x + (Math.random()-0.5)*S*2;
       p.y = pc.y + (Math.random()-0.5)*S*2;
    } else {
       p.x = W/2;
       p.y = H/2;
    }
    // 节点大小随被引量变化
    p.r = Math.min(25, Math.max(3, 4 + Math.sqrt(p.citations || 0)));
  });

  const simulation = d3.forceSimulation([...categories, ...papers])
    .force('link', d3.forceLink(G.edges).id(d=>d.id).distance(d=>d.type==='paper_sim'?150:80).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-150))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(n => n.r + 5));

  const ge = d3.select('#ge');
  const gn = d3.select('#gn');

  const link = ge.selectAll('line').data(G.edges).join('line')
    .attr('stroke', d => d.type === 'paper_sim' ? '#58a6ff' : '#484f58')
    .attr('stroke-opacity', 0.4)
    .attr('stroke-width', d => d.weight || 1);

  const node = gn.selectAll('g').data([...categories, ...papers]).join('g')
    .attr('cursor','pointer')
    .call(d3.drag()
      .on('start', (e,d) => { if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on('drag',  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on('end',   (e,d) => { if(!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; })
    );

  node.append('circle')
    .attr('r', d => d.r)
    .attr('fill', d => d.color)
    .attr('fill-opacity', d => d.type==='category'?0.3:0.9)
    .attr('stroke', d => d.color)
    .attr('stroke-width', d => d.type==='category'?2:0);

  node.append('text')
    .text(d => d.label)
    .attr('text-anchor', 'middle')
    .attr('dy', d => d.r + 12)
    .attr('font-size', d => d.type==='category'?'14px':'10px')
    .attr('fill', d => d.type==='category'?'#ffffff':'#8b949e')
    .attr('font-weight', d => d.type==='category'?'bold':'normal')
    .style('pointer-events', 'none');

  node.on('click', (_,d)=>showInfo(d));

  simulation.on('tick', () => {
    link.attr('x1', d=>d.source.x).attr('y1', d=>d.source.y)
        .attr('x2', d=>d.target.x).attr('y2', d=>d.target.y);
    node.attr('transform', d=>`translate(${d.x},${d.y})`);
  });
}

svg = d3.select('#svg');
root = d3.select('#root');
svg.call(d3.zoom().scaleExtent([0.1, 8]).on('zoom', e=>{root.attr('transform', e.transform); }));

render();

setTimeout(()=>{
  const firstCat = G.nodes.find(n=>n.type==='category');
  if(firstCat) showInfo(firstCat);
}, 500);
</script>
</body></html>
'''

def main():
    with open(GRAPH_JSON, 'r', encoding='utf-8') as f:
        gdata = f.read()
    html = HTML_TPL.replace('{GRAPH_DATA}', gdata)
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Done: {OUT_HTML}')

if __name__ == '__main__':
    main()