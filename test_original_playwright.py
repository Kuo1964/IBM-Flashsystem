from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def fetch_rendered_html_with_playwright(url: str) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome", headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
            )
            Stealth().apply_stealth_sync(page)
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            html = page.content()
            for frame in page.frames:
                try:
                    frame_content = frame.content()
                    if len(frame_content) > 500:
                        html += "\n" + frame_content
                except Exception:
                    pass
            browser.close()
            return html
    except Exception as e:
        print(f"[警告] Playwright 渲染網頁失敗 ({url}): {e}")
        return ""

print("🚀 測試「原始版本」的 Playwright 網頁抓取邏輯...")
html = fetch_rendered_html_with_playwright("https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=software-feature-guide")
print("抓取回傳長度:", len(html))
if len(html) > 0:
    if "digitalData" in html or "IBM" in html:
        print("✅ 成功！抓到有效的網頁內容。")
    else:
        print("⚠️ 抓到了網頁，但沒有 IBM 關鍵字。")
else:
    print("❌ 失敗：回傳空字串 (例外被吞噬了)")
