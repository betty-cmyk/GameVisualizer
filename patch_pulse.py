import re
with open('graph_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 把粗暴的全天候 requestAnimationFrame 动画循环删掉
html = html.replace("            // 【持续动画驱动】：启动全局 requestAnimationFrame 维持脉冲线的无限流动！\n            function animate() {\n                render();\n                requestAnimationFrame(animate);\n            }\n            animate();", "            render();")

# 2. 加入按需驱动的极客动画调度器，并修改 setEdgeMode
mode_old = """let activeEdgeMode = 'sim'; 
function setEdgeMode(mode) {
    activeEdgeMode = mode;
    document.getElementById('btn-sim').classList.remove('active');
    document.getElementById('btn-cite').classList.remove('active');
    document.getElementById(`btn-${mode}`).classList.add('active');
    render(); 
}"""
mode_new = """let activeEdgeMode = 'sim'; 
let animationFrameId = null;

function startPulseAnimation() {
    if (animationFrameId) return;
    function pulse() {
        render();
        animationFrameId = requestAnimationFrame(pulse);
    }
    pulse();
}
function stopPulseAnimation() {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
}

function setEdgeMode(mode) {
    activeEdgeMode = mode;
    document.getElementById('btn-sim').classList.remove('active');
    document.getElementById('btn-cite').classList.remove('active');
    document.getElementById(`btn-${mode}`).classList.add('active');
    
    if (mode === 'cite') startPulseAnimation();
    else { stopPulseAnimation(); render(); }
}"""
html = html.replace(mode_old, mode_new)

# 3. 取消选中时停止脉冲
close_old = """function closeDetail() {
  document.getElementById('d-edge-mode-box').style.display = 'none';"""
close_new = """function closeDetail() {
  stopPulseAnimation();
  document.getElementById('d-edge-mode-box').style.display = 'none';"""
html = html.replace(close_old, close_new)

# 4. 在 search 或者初始化 focusNode 点击进入引用模式（如果有记忆）时启动脉冲
focus_old = """    selectedNode = n;
    showDetail(selectedNode); """
focus_new = """    selectedNode = n;
    if (activeEdgeMode === 'cite') startPulseAnimation();
    showDetail(selectedNode); """
html = html.replace(focus_old, focus_new)

# 5. 确保画线前清空虚线模式 (防止背景白丝被污染成虚线)
render_old = """    // 【灵魂补回】：绘制满天星辰的背景引力网（淡弱的语义相似线）
    ctx.beginPath();"""
render_new = """    // 保证背景相似引力网永远是极其纯洁的安静实线！
    ctx.setLineDash([]); 
    ctx.lineDashOffset = 0;
    ctx.shadowBlur = 0;
    // 【灵魂补回】：绘制满天星辰的背景引力网（淡弱的语义相似线）
    ctx.beginPath();"""
html = html.replace(render_old, render_new)

with open('graph_template.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Pulse Animation successfully tuned for cited mode only!")
