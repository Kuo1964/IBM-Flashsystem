"""
單本 PDF 下載功能獨立驗證腳本 (支援 Playwright WAF 穿透與動態真實連結解析)
"""
import os
from pathlib import Path
from urllib.parse import urljoin

TARGET_URL = "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.1?topic=download-pdf"
OUTPUT_DIR = Path("raw_data/pdfs")

def verify_single_pdf():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🔍 開始執行單本 PDF 下載驗證 (Playwright WAF 穿透模式)")
    print("=" * 60)
    print(f"1. 目標入口網址: {TARGET_URL}")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 錯誤：尚未安裝 Playwright，請先執行 pip install playwright")
        return False

    with sync_playwright() as p:
        print("2. 正在啟動 Chromium 瀏覽器實例...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"3. 正在載入頁面並解析動態 DOM...")
        page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        # 取得所有 <a> 標籤的完整解析連結 (由瀏覽器原生解析)
        links = page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText}))")
        
        pdf_links = [item for item in links if item["href"] and item["href"].lower().endswith(".pdf")]
        
        if not pdf_links:
            print("❌ 頁面中未找到任何 .pdf 結尾的連結。")
            browser.close()
            return False
            
        print(f"4. 成功在頁面中找到 {len(pdf_links)} 個 PDF 連結。")
        first_pdf = pdf_links[0]
        pdf_url = first_pdf["href"]
        pdf_name = pdf_url.split("/")[-1].split("?")[0]
        
        print(f"5. 選定第 1 本 PDF 進行下載驗證:")
        print(f"   - 標題/說明: {first_pdf['text'].strip() or '無文字'}")
        print(f"   - 檔案名稱: {pdf_name}")
        print(f"   - 完整下載網址: {pdf_url}")
        
        print(f"6. 正在透過 Playwright Context 發起二進位下載 (繞過 WAF)...")
        response = context.request.get(pdf_url)
        print(f"   HTTP 回應狀態碼: {response.status}")
        
        if response.ok:
            body = response.body()
            if body.startswith(b"%PDF-"):
                file_size_mb = len(body) / (1024 * 1024)
                save_path = OUTPUT_DIR / pdf_name
                with open(save_path, "wb") as f:
                    f.write(body)
                print("-" * 60)
                print(f"🎉 驗證成功！")
                print(f"   - 檔案名稱: {pdf_name}")
                print(f"   - 檔案大小: {file_size_mb:.2f} MB")
                print(f"   - 儲存路徑: {save_path}")
                print(f"   - 二進位標頭確認: %PDF- 格式正確無誤")
                print("-" * 60)
                browser.close()
                return True
            else:
                print("❌ 警告：狀態碼為 200，但內容並非有效 PDF。")
        else:
            print(f"❌ 下載失敗，狀態碼: {response.status}")
            
        browser.close()
    return False

if __name__ == "__main__":
    verify_single_pdf()
