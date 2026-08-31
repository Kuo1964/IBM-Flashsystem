import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# 目標網址
TARGET_URL = "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.3?topic=download-pdf"
# 下載存放路徑
DOWNLOAD_DIR = "raw_data/pdfs"

def main():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    print(f"啟動 Playwright 無頭瀏覽器...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 建立 context 以繼承瀏覽器指紋與 Cookie，避免被 WAF 阻擋
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"正在載入網頁: {TARGET_URL}")
        page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
        
        # 等待頁面動態渲染完成
        page.wait_for_timeout(3000)
        
        # 尋找所有 <a> 標籤的 href 屬性
        hrefs = page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")
        
        # 過濾出 .pdf 結尾的網址
        pdf_links = set([href for href in hrefs if href and href.lower().endswith(".pdf")])
        
        if not pdf_links:
            print("未在頁面中找到任何 PDF 連結。")
        else:
            print(f"共找到 {len(pdf_links)} 個 PDF 檔案，準備開始下載...")
            
            for pdf_url in pdf_links:
                file_name = pdf_url.split("/")[-1]
                save_path = os.path.join(DOWNLOAD_DIR, file_name)
                
                print(f"正在下載: {file_name} ...", end=" ", flush=True)
                
                # 透過 Playwright 的原生 request API 下載，以繞過 IBM 的 403 WAF 阻擋
                response = context.request.get(pdf_url)
                
                if response.ok:
                    with open(save_path, "wb") as f:
                        f.write(response.body())
                    print("✅ 完成")
                else:
                    print(f"❌ 失敗 (HTTP {response.status})")
                    
        browser.close()
        print("所有下載任務結束！")

if __name__ == "__main__":
    main()
