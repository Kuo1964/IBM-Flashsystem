"""
IBM FlashSystem 官方技術手冊 - 單本 PDF 獨立下載與驗證工具
採用 Playwright 瀏覽器核心動態解析真實絕對 URL，並透過 Context Request 穿透 WAF 下載
"""
import os
import sys
from pathlib import Path

TARGET_URL = "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.1?topic=download-pdf"
OUTPUT_DIR = Path("raw_data/pdfs")

def run_single_download():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print("🚀 啟動獨立單本 PDF 下載驗證程式 (Playwright DOM 穿透架構)")
    print("=" * 65)
    print(f"1. 目標入口頁面: {TARGET_URL}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 錯誤：尚未安裝 Playwright，請先執行 pip install playwright")
        return False

    with sync_playwright() as p:
        print("2. 啟動 Chromium 瀏覽器並配置真實環境指紋...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("3. 正在載入頁面並等待動態 SPA 路由生成...")
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        print("4. 透過瀏覽器核心提取真實解析完成之絕對 PDF 下載網址...")
        # 關鍵核心：由 Chromium 引擎直接解析完整的真實絕對路徑
        links = page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))")
        pdf_links = [item for item in links if item["href"] and ".pdf" in item["href"].lower()]

        if not pdf_links:
            print("❌ 頁面中未找到任何 PDF 連結，請確認入口網址。")
            browser.close()
            return False

        print(f"   共找到 {len(pdf_links)} 個技術手冊連結！")
        target_pdf = pdf_links[0]
        pdf_url = target_pdf["href"].split("#")[0]
        file_name = pdf_url.split("/")[-1].split("?")[0]
        if not file_name.endswith(".pdf"):
            file_name += ".pdf"

        print(f"\n📂 選定第 1 本手冊進行下載驗證:")
        print(f"   - 手冊標題: {target_pdf['text'] or 'IBM FlashSystem Guide'}")
        print(f"   - 檔案名稱: {file_name}")
        print(f"   - 官方真實下載路徑: {pdf_url}")

        print(f"\n5. 正在透過瀏覽器 Session 下載二進位檔案...")
        response = context.request.get(pdf_url, timeout=60000)
        print(f"   HTTP 狀態碼: {response.status}")

        if response.ok:
            body = response.body()
            if body.startswith(b"%PDF-"):
                file_size_mb = len(body) / (1024 * 1024)
                save_path = OUTPUT_DIR / file_name
                with open(save_path, "wb") as f:
                    f.write(body)
                print("=" * 65)
                print(f"🎉 下載驗證成功！")
                print(f"   - 儲存位置: {save_path}")
                print(f"   - 檔案大小: {file_size_mb:.2f} MB")
                print(f"   - 格式校驗: %PDF- 二進位格式正確無誤")
                print("=" * 65)
                browser.close()
                return True
            else:
                print("❌ 警告：伺服器回傳 200，但內容不是有效的 PDF 檔案。")
        else:
            print(f"❌ 下載失敗，狀態碼: {response.status}")

        browser.close()
    return False

if __name__ == "__main__":
    run_single_download()
