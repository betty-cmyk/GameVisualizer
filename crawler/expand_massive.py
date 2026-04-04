# -*- coding: utf-8 -*-
import sqlite3, json, time, re, random, threading
import tkinter as tk
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "papers.db"
JSON_CLEAN = ROOT / "data" / "papers_clean.json"
PROGRESS_FILE = ROOT / "data" / "progress.json"

class CrawlerState:
    paused = True
    stopped = False
    status_msg = "准备就绪，请设置休眠后点击【开始】"
    current_target = ""
    query_idx = 0
    page_idx = 1
    wait_time = 15

state = CrawlerState()

SEARCH_QUERIES = [
    {'cat': 'Rendering', 'q': '"real-time rendering" OR "ray tracing" OR "global illumination" game'},
    {'cat': 'Rendering', 'q': '"neural rendering" OR "NeRF" OR "3D Gaussian Splatting"'},
    {'cat': 'PCG', 'q': '"procedural content generation" OR "PCG" OR "terrain generation" game'},
    {'cat': 'PCG', 'q': '"procedural modeling" OR "level generation" game'},
    {'cat': 'Game AI', 'q': '"reinforcement learning" OR "pathfinding" OR "behavior tree" NPC'},
    {'cat': 'Game AI', 'q': '"game AI" OR "automated playtesting"'},
    {'cat': 'Animation', 'q': '"character animation" OR "motion capture" OR "motion synthesis" game'},
    {'cat': 'Simulation & Physics', 'q': '"physics simulation" OR "collision detection" OR "fluid simulation" game'},
    {'cat': 'HCI/UX in Games', 'q': '"player experience" OR "game user research" OR "virtual reality" game'},
    {'cat': 'Networking & Systems', 'q': '"cloud gaming" OR "game engine" architecture'},
    {'cat': 'Game Analytics', 'q': '"game analytics" OR "player behavior" matchmaking'}
]

def classify_paper(title, abstract):
    text = (title + " " + abstract).lower()
    if any(k in text for k in ["rendering", "ray tracing", "illumination", "shading", "nerf", "gaussian"]): return "Rendering"
    if any(k in text for k in ["pcg", "procedural", "terrain", "level generation"]): return "PCG"
    if any(k in text for k in ["ai", "reinforcement", "pathfinding", "npc", "bot", "agent"]): return "Game AI"
    if any(k in text for k in ["animation", "motion", "kinematics", "rigging"]): return "Animation"
    if any(k in text for k in ["physics", "simulation", "collision", "fluid", "cloth"]): return "Simulation & Physics"
    if any(k in text for k in ["hci", "player experience", "ux", "vr", "ar"]): return "HCI/UX in Games"
    if any(k in text for k in ["network", "latency", "cloud gaming", "synchronization"]): return "Networking & Systems"
    if any(k in text for k in ["analytics", "behavior", "matchmaking", "serious game"]): return "Game Analytics"
    return "Game AI"

def extract_year(text):
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return int(match.group(1)) if match else 2024

def is_blocked(driver):
    try:
        src, title = driver.page_source.lower(), driver.title.lower()
        if "sorry/index" in src or "unusual traffic" in src or "recaptcha" in src: return True
        if "sorry" in title or "robot" in title or "人机身份验证" in title: return True
        return False
    except:
        return True

def crawler_thread(ui_update_callback):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        state.status_msg = "[!] 无法接管浏览器(9222端口未开)"
        ui_update_callback()
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, author TEXT, unit TEXT, degree TEXT, year INTEGER, abstract TEXT,
        outline TEXT, keywords TEXT, category_9 TEXT, directions TEXT, source_kw TEXT,
        db_type TEXT, db_source TEXT, source_url TEXT, source_site TEXT)''')
    
    cur.execute("SELECT title FROM papers")
    existing_titles = {row[0].replace(" ", "").lower() for row in cur.fetchall()}
    
    state.status_msg = "开始自动化深潜..."
    ui_update_callback()
    
    PAGES_PER_QUERY = 15
    new_papers = 0
    
    try:
        while state.query_idx < len(SEARCH_QUERIES):
            if state.stopped: break
            
            # --- 挂起与状态检测 --- 
            while state.paused or is_blocked(driver):
                if not state.paused and is_blocked(driver):
                    state.paused = True
                    state.status_msg = "🚨 发现人机验证！已暂停。验证后点击【继续】"
                    ui_update_callback()
                time.sleep(0.5)
                if state.stopped: break
            if state.stopped: break
            
            item = SEARCH_QUERIES[state.query_idx]
            cat, q = item['cat'], item['q']
            
            state.current_target = f"[{cat}] {q} (第{state.page_idx}页)"
            state.status_msg = f"正在抓取中..."
            ui_update_callback()
            
            # 直接通过 Start 参数翻页
            start_param = (state.page_idx - 1) * 10
            url = f"https://scholar.google.com/scholar?hl=en&q={urllib.parse.quote(q)}&start={start_param}"
            
            try: driver.get(url)
            except: pass
            
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".gs_ri")))
                
                blocks = driver.find_elements(By.CSS_SELECTOR, ".gs_ri")
                for b in blocks:
                    try:
                        title_el = b.find_element(By.CSS_SELECTOR, ".gs_rt a")
                        title = title_el.text.strip()
                        clean_title = title.replace(" ", "").lower()
                        title = re.sub(r'^\[.*?\]\s*', '', title)
                        if clean_title in existing_titles: continue
                        
                        source_url = title_el.get_attribute("href")
                        meta = b.find_element(By.CSS_SELECTOR, ".gs_a").text.strip()
                        author = meta.split('-')[0].strip() if '-' in meta else ""
                        year = extract_year(meta)
                        
                        abstract = ""
                        try: abstract = b.find_element(By.CSS_SELECTOR, ".gs_rs").text.strip()
                        except: pass
                        
                        real_cat = classify_paper(title, abstract)
                        cur.execute("""INSERT INTO papers (title, author, year, abstract, source_url, category_9, directions, db_source)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                                    (title, author, year, abstract, source_url, real_cat, real_cat, "GoogleScholar_Game"))
                        conn.commit()
                        existing_titles.add(clean_title)
                        new_papers += 1
                        state.status_msg = f"已入库 {new_papers} 篇新论文"
                        ui_update_callback()
                    except: continue
                    
                # 抓取完本页后，进入防封禁休眠倒计时
                # 如果在这里面被点“暂停”，或者再被点“继续”，由于最外层的 while 会立刻打断这个循环
                # 从而实现“暂停->继续=立刻翻下一页抓取”的效果！
                if state.page_idx < PAGES_PER_QUERY:
                    sleep_t = random.uniform(state.wait_time, state.wait_time + 4.0)
                    steps = int(sleep_t * 10)
                    for s in range(steps, 0, -1):
                        if state.paused or state.stopped: 
                            break # 只要一点暂停，立刻打破倒计时！
                        if s % 10 == 0:
                            state.status_msg = f"防封禁休眠中... 剩余 {s//10} 秒"
                            ui_update_callback()
                        time.sleep(0.1)
                        
                state.page_idx += 1
                
            except:
                state.status_msg = f"第 {state.page_idx} 页无结果或被拦截，切换下一词"
                ui_update_callback()
                state.query_idx += 1
                state.page_idx = 1
                time.sleep(2)
                continue
                
            if state.page_idx > PAGES_PER_QUERY:
                state.query_idx += 1
                state.page_idx = 1
                
    except Exception as e:
        print(f"Crawler Error: {e}")
    finally:
        state.status_msg = f"任务结束！本次共抓取 {new_papers} 篇"
        state.stopped = True
        ui_update_callback()
        
        if new_papers > 0:
            cur.execute("PRAGMA table_info(papers)")
            cols = [d[1] for d in cur.fetchall()]
            cur.execute("SELECT * FROM papers")
            data = json.loads(JSON_CLEAN.read_text(encoding='utf-8')) if JSON_CLEAN.exists() else {'papers': []}
            data['papers'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            JSON_CLEAN.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        conn.close()

# ================= GUI 控制面板 =================
def start_gui():
    root = tk.Tk()
    root.title("Game学术抓取控制台")
    root.geometry("350x200")
    root.attributes('-topmost', True)
    root.configure(bg="#1e1e1e")
    
    lbl_target = tk.Label(root, text="Target: Waiting...", fg="#58a6ff", bg="#1e1e1e", wraplength=330, font=("Microsoft YaHei", 9))
    lbl_target.pack(pady=10)
    
    lbl_status = tk.Label(root, text="Status: Starting...", fg="#3fb950", bg="#1e1e1e", wraplength=330, font=("Microsoft YaHei", 10, "bold"))
    lbl_status.pack(pady=10)
    
    frame_params = tk.Frame(root, bg="#1e1e1e")
    frame_params.pack(pady=5)
    tk.Label(frame_params, text="基础休眠(5-25秒):", fg="white", bg="#1e1e1e", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
    entry_wait = tk.Entry(frame_params, width=8, font=("Microsoft YaHei", 9))
    entry_wait.insert(0, "15")
    entry_wait.pack(side=tk.LEFT, padx=5)
    
    def apply_wait_time():
        try:
            wt = int(entry_wait.get())
            wt = max(5, min(wt, 30))
            state.wait_time = wt
            entry_wait.delete(0, tk.END)
            entry_wait.insert(0, str(wt))
        except:
            entry_wait.delete(0, tk.END)
            entry_wait.insert(0, str(state.wait_time))

    def toggle_pause():
        apply_wait_time()
        if state.paused:
            state.paused = False
            btn_pause.config(text="⏸️ 暂停", bg="#e3b341")
            lbl_status.config(fg="#3fb950")
        else:
            state.paused = True
            btn_pause.config(text="▶️ 开始/继续", bg="#3fb950")
            lbl_status.config(text="已手动暂停", fg="#f85149")
            
    def save_progress():
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"query_idx": state.query_idx, "page_idx": state.page_idx}, f)
            state.status_msg = f"进度已保存! (词条:{state.query_idx}, 页:{state.page_idx})"
            update_ui()
        except: pass
            
    def load_progress():
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    p = json.load(f)
                    state.query_idx = p.get("query_idx", 0)
                    state.page_idx = p.get("page_idx", 1)
                state.status_msg = f"进度已读取!"
                update_ui()
            except: pass
            
    def update_ui():
        lbl_target.config(text=f"目标: {state.current_target}")
        if not state.paused:
            lbl_status.config(text=state.status_msg)
            if "🚨" in state.status_msg:
                lbl_status.config(fg="#f85149")
                btn_pause.config(text="▶️ 已验证,点击继续", bg="#3fb950")
            else:
                lbl_status.config(fg="#3fb950")
                btn_pause.config(text="⏸️ 暂停", bg="#e3b341")

    btn_frame1 = tk.Frame(root, bg="#1e1e1e")
    btn_frame1.pack(pady=5)
    btn_pause = tk.Button(btn_frame1, text="▶️ 开始/继续", bg="#3fb950", fg="black", font=("Microsoft YaHei", 9, "bold"), command=toggle_pause, width=12)
    btn_pause.grid(row=0, column=0, padx=10)
    
    btn_frame2 = tk.Frame(root, bg="#1e1e1e")
    btn_frame2.pack(pady=5)
    tk.Button(btn_frame2, text="💾 保存进度", bg="#58a6ff", fg="white", font=("Microsoft YaHei", 9, "bold"), command=save_progress, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame2, text="📂 读取进度", bg="#58a6ff", fg="white", font=("Microsoft YaHei", 9, "bold"), command=load_progress, width=10).pack(side=tk.LEFT, padx=5)
    
    t = threading.Thread(target=crawler_thread, args=(lambda: root.after(0, update_ui),))
    t.daemon = True
    t.start()
    
    root.mainloop()

if __name__ == '__main__':
    start_gui()