"""
IBM FlashSystem 全版本官方技術手冊 (PDFs) 批量自動收割工具
支援 9.1.x, 8.7.x, 8.6.x, 8.5.x 全系列產品手冊自動化發現、WAF 穿透與二進位驗證
"""
import os
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path("raw_data/pdfs")
URLS_FILE = Path("raw_data/web_urls.txt")
FAILED_LOG = Path("raw_data/failed_pdf_downloads.log")

def get_target_pdf_pages() -> list:
    """從 web_urls.txt 讀取並產生各版本的 PDF 下載專區網址"""
    if not URLS_FILE.exists():
        return []
    pages = []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                base = line.split("?")[0].rstrip("/")
                pdf_page = f"{base}?topic=download-pdf"
                pages.append(pdf_page)
    return pages

def run_bulk_download():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target_pages = get_target_pdf_pages()
    
    print("=" * 70)
    print(f"🚀 啟動 IBM FlashSystem 全版本 PDF 批量收割引擎 (共 {len(target_pages)} 個版本專區)")
    print("=" * 70)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 錯誤：尚未安裝 Playwright，請先執行 pip install playwright")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        discovered_pdfs = {}
        for idx, pdf_page_url in enumerate(target_pages, 1):
            print(f"\n🔍 [{idx}/{len(target_pages)}] 正在探索版本專區: {pdf_page_url}")
            try:
                page.goto(pdf_page_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3500)
                
                links = page.eval_on_selector_all("a", "elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))")
                count_this_page = 0
                for item in links:
                    href = item.get("href", "")
                    if href and ".pdf" in href.lower():
                        clean_url = href.split("#")[0]
                        file_name = clean_url.split("/")[-1].split("?")[0]
                        if not file_name.endswith(".pdf"):
                            file_name += ".pdf"
                        if file_name not in discovered_pdfs:
                            discovered_pdfs[file_name] = {
                                "url": clean_url,
                                "title": item.get("text") or file_name,
                                "source_page": pdf_page_url
                            }
                            count_this_page += 1
                print(f"   ├─ 本專區新增 {count_this_page} 本，目前全域累計 {len(discovered_pdfs)} 本官方技術手冊")
            except Exception as e:
                print(f"   └─ [警告] 探索專區失敗 ({pdf_page_url}): {e}")

        # 開始批量下載
        print("\n" + "=" * 70)
        print(f"📥 開始執行二進位下載作業 (共需檢驗/下載 {len(discovered_pdfs)} 本手冊)...")
        print("=" * 70)

        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, (file_name, info) in enumerate(discovered_pdfs.items(), 1):
            save_path = OUTPUT_DIR / file_name
            if save_path.exists() and save_path.stat().st_size > 1024 * 100:
                print(f"[{i}/{len(discovered_pdfs)}] ⏩ [已存在跳過] {file_name}")
                skip_count += 1
                continue

            print(f"[{i}/{len(discovered_pdfs)}] ⏳ 正在下載: {file_name} ...", end=" ", flush=True)
            downloaded = False
            for attempt in range(3):
                try:
                    res = context.request.get(info["url"], timeout=60000)
                    if res.ok:
                        body = res.body()
                        if body.startswith(b"%PDF-"):
                            with open(save_path, "wb") as f:
                                f.write(body)
                            size_mb = len(body) / (1024 * 1024)
                            print(f"✅ 完成 ({size_mb:.2f} MB)")
                            success_count += 1
                            downloaded = True
                            break
                    time.sleep(1.0)
                except Exception:
                    time.sleep(1.5)

            if not downloaded:
                print("❌ 失敗")
                fail_count += 1
                with open(FAILED_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{file_name}\t{info['url']}\n")

            time.sleep(0.5)

        browser.close()
        print("\n" + "=" * 70)
        print(f"🎉 批量收割任務結束！")
        print(f"   - 新增下載: {success_count} 本")
        print(f"   - 本地已存在: {skip_count} 本")
        print(f"   - 下載失敗: {fail_count} 本")
        print(f"   - 檔案儲存目錄: {OUTPUT_DIR}")
        print("=" * 70)

if __name__ == "__main__":
    run_bulk_download()
