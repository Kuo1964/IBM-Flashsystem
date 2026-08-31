import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def fetch(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome", headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
            except:
                pass
            page.wait_for_timeout(2000)
            html = page.content()
            for frame in page.frames:
                try:
                    fc = frame.content()
                    if len(fc) > 500:
                        html += "\\n" + fc
                except:
                    pass
            browser.close()
            print(html)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

if __name__ == "__main__":
    fetch(sys.argv[1])
