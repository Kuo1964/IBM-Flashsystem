import re

with open("parser.py", "r", encoding="utf-8") as f:
    content = f.read()

# Define the new global state and the rewritten function
new_func = """_playwright_instance = None
_browser_instance = None
_browser_page_count = 0

def fetch_rendered_html_with_playwright(url: str) -> str:
    \"\"\"使用 Playwright 無頭瀏覽器渲染動態 JavaScript 網頁 (全局守護進程模式)\"\"\"
    global _playwright_instance, _browser_instance, _browser_page_count
    
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth
        
        # 1. 初始化全局瀏覽器 (若尚未啟動)
        if _playwright_instance is None:
            _playwright_instance = sync_playwright().start()
            _browser_instance = _playwright_instance.chromium.launch(
                channel="chrome", 
                headless=True, 
                args=['--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage', '--no-sandbox']
            )
            _browser_page_count = 0
            
        # 2. 定期重啟以防止記憶體洩漏 (每處理 200 頁重啟一次)
        _browser_page_count += 1
        if _browser_page_count > 200:
            print(f"  [維護] 重啟 Playwright 瀏覽器釋放記憶體...")
            try:
                _browser_instance.close()
                _playwright_instance.stop()
            except:
                pass
            _playwright_instance = sync_playwright().start()
            _browser_instance = _playwright_instance.chromium.launch(
                channel="chrome", 
                headless=True, 
                args=['--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage', '--no-sandbox']
            )
            _browser_page_count = 1
            
        # 3. 開啟新分頁進行抓取
        context = _browser_instance.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        try:
            # 延長 timeout 並等待 networkidle
            page.goto(url, wait_until="networkidle", timeout=25000)
        except Exception as e:
            # 如果超時，仍可嘗試提取目前的內容
            pass
            
        page.wait_for_timeout(2000)
        
        html = page.content()
        for frame in page.frames:
            try:
                frame_content = frame.content()
                if len(frame_content) > 500:
                    html += "\\n" + frame_content
            except:
                pass
                
        context.close()
        return html
        
    except Exception as e:
        print(f"[警告] Playwright 渲染網頁失敗 ({url}): {e}")
        # 若發生核心驅動錯誤，強制下次重啟
        _playwright_instance = None
        return ""
"""

# Find the old function and replace it
import ast
class FuncFinder(ast.NodeVisitor):
    def __init__(self):
        self.start_lineno = None
        self.end_lineno = None
        self.decorator_list = []
    
    def visit_FunctionDef(self, node):
        if node.name == "fetch_rendered_html_with_playwright":
            self.start_lineno = node.lineno
            self.end_lineno = node.end_lineno
            self.decorator_list = node.decorator_list
        self.generic_visit(node)

tree = ast.parse(content)
finder = FuncFinder()
finder.visit(tree)

if finder.start_lineno:
    lines = content.splitlines()
    # Replace from start_lineno-1 to end_lineno
    before = lines[:finder.start_lineno-1]
    after = lines[finder.end_lineno:]
    
    new_content = "\n".join(before) + "\n\n" + new_func + "\n" + "\n".join(after)
    with open("parser.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched parser.py successfully.")
else:
    print("Function not found!")

