"""
IBM FlashSystem 專家系統 - 文件與圖片解析器 (支援動態 JS/SPA 網頁 Playwright 渲染與目錄子頁面遞迴爬取)
"""

import hashlib
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
from urllib.parse import urlparse, urljoin
import fitz  # PyMuPDF
from PIL import Image
import httpx
from bs4 import BeautifulSoup

import config

def calculate_file_hash(file_path: Path) -> str:
    """計算檔案的 SHA-256 Hash 值，用於增量更新比對"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def create_text_chunks(text: str, source_name: str, page_num: int = 0) -> List[Dict[str, Any]]:
    """將文字分割為固定大小與重疊度的語意片段 (Chunks)"""
    chunks = []
    text = text.strip()
    if not text:
        return chunks

    start = 0
    chunk_idx = 0
    while start < len(text):
        end = start + config.CHUNK_SIZE
        chunk_text = text[start:end]
        
        chunks.append({
            "chunk_id": f"{source_name}_p{page_num}_c{chunk_idx}",
            "text": chunk_text,
            "metadata": {
                "source": source_name,
                "page": page_num,
                "type": "text",
                "chunk_index": chunk_idx
            }
        })
        chunk_idx += 1
        start += (config.CHUNK_SIZE - config.CHUNK_OVERLAP)

    return chunks

def parse_pdf(pdf_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """解析 PDF 檔案，提取文字與技術圖表圖片 (具備記憶體安全與 C-level Crash 防護)"""
    pdf_name = pdf_path.stem
    text_chunks = []
    image_records = []

    pdf_image_dir = config.EXTRACTED_IMAGES_DIR / pdf_name
    pdf_image_dir.mkdir(parents=True, exist_ok=True)

    try:
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    actual_page = page_num + 1
                    
                    # 使用基礎純文字提取，避免損毀字型觸發 C 崩潰
                    try:
                        page_text = page.get_text("text", flags=fitz.TEXTFLAGS_SEARCH)
                    except Exception:
                        page_text = page.get_text("text")

                    if page_text and page_text.strip():
                        page_chunks = create_text_chunks(page_text, source_name=pdf_name, page_num=actual_page)
                        text_chunks.extend(page_chunks)

                    # 嘗試提取圖片，若圖片列表損毀則平滑略過
                    try:
                        image_list = page.get_images(full=True)
                    except Exception:
                        image_list = []

                    for img_idx, img_info in enumerate(image_list):
                        if not img_info or len(img_info) < 1:
                            continue
                        xref = img_info[0]
                        try:
                            base_image = doc.extract_image(xref)
                            if not base_image or "image" not in base_image:
                                continue
                            
                            image_bytes = base_image["image"]
                            if not image_bytes or len(image_bytes) < 100:
                                continue

                            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                                width, height = pil_img.size

                                if width >= config.MIN_IMAGE_WIDTH and height >= config.MIN_IMAGE_HEIGHT:
                                    img_filename = f"page_{actual_page}_img_{img_idx}.jpg"
                                    save_path = pdf_image_dir / img_filename
                                    
                                    # 安全轉為 RGB 模式防範 CMYK/Palette 解碼 Segfault
                                    rgb_img = pil_img.convert("RGB")
                                    rgb_img.save(save_path, "JPEG", quality=90)

                                    image_records.append({
                                        "image_id": f"{pdf_name}_p{actual_page}_img{img_idx}",
                                        "image_path": str(save_path),
                                        "pdf_name": pdf_name,
                                        "page_number": actual_page,
                                        "width": width,
                                        "height": height
                                    })
                        except Exception:
                            # 個別損毀圖片跳過防護
                            continue

                except Exception as page_err:
                    print(f"  [警告] 處理 PDF 頁面失敗 ({pdf_name} 第 {page_num + 1} 頁): {page_err}")
                    continue
    except Exception as doc_err:
        print(f"  [錯誤] 開啟 PDF 檔案失敗 ({pdf_path.name}): {doc_err}")

    return text_chunks, image_records


_playwright_instance = None
_browser_instance = None
_browser_page_count = 0

def fetch_rendered_html_with_playwright(url: str) -> str:
    """使用 Playwright 無頭瀏覽器渲染動態 JavaScript 網頁 (全局守護進程模式)"""
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
            import random
            import time
            # 隨機延遲 1~4 秒，錯開 3 個 worker 的請求，降低 WAF 封鎖機率
            time.sleep(random.uniform(3.0, 8.0))
            # 延長 timeout 並等待 networkidle
            page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            # 如果超時，仍可嘗試提取目前的內容
            pass
            
        page.wait_for_timeout(2000)
        
        html = page.content()
        for frame in page.frames:
            try:
                frame_content = frame.content()
                if len(frame_content) > 500:
                    html += "\n" + frame_content
            except:
                pass
                
        context.close()
        return html
        
    except Exception as e:
        print(f"[警告] Playwright 渲染網頁失敗 ({url}): {e}")
        # 若發生核心驅動錯誤，強制下次重啟
        _playwright_instance = None
        return ""


def extract_clean_page_content(html_content: str) -> Tuple[str, List[str]]:
    """從 HTML 內文中提取純文字與所有包含的超連結"""
    from bs4 import BeautifulSoup
    import markdownify
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
            links.append(href)

    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()

    md_text = markdownify.markdownify(str(soup), heading_style="ATX", escape_asterisks=False, bullets="-")
    
    if "403: Forbidden" in md_text and "The page you requested cannot be displayed" in md_text:
        print(f"  [防護攔截] 網頁回傳 WAF 403 Forbidden，拋棄無效 Chunk 以免污染資料庫。")
        return "", []
    
    lines = [line.strip() for line in md_text.splitlines()]
    clean_lines = []
    for line in lines:
        if line or (clean_lines and clean_lines[-1]):
            clean_lines.append(line)
            
    full_text = "\n".join(clean_lines).strip()

    return full_text, links

def parse_single_page(url: str) -> Dict[str, Any]:
    """
    只抓取單一網頁，萃取 Chunks 與該頁面上的所有超連結。
    """
    url = url.strip()
    clean_target_url = url.split("#")[0]
    
    base_parsed = urlparse(url)
    base_domain = base_parsed.netloc
    base_path_prefix = "/".join(base_parsed.path.rstrip("/").split("/")[:-1])

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    result = {"url": clean_target_url, "chunks": [], "links": [], "error": None}

    try:
        html_content = ""
        response = httpx.get(clean_target_url, headers=headers, timeout=60000.0, follow_redirects=True)
        if response.status_code == 200:
            html_content = response.text

        if len(html_content) < 2000 or "digitalData" in html_content or "ibm.com/docs" in clean_target_url:
            rendered = fetch_rendered_html_with_playwright(clean_target_url)
            if rendered and len(rendered) > 2000:
                html_content = rendered
            else:
                raise Exception("Playwright 渲染失敗或返回空內容，觸發 Rollback")

        if not html_content:
            result["error"] = "Empty content"
            return result

        page_text, raw_links = extract_clean_page_content(html_content)
        
        if not page_text:
            result["error"] = "No extractable text"
            return result
            
        source_name = hashlib.md5(clean_target_url.encode()).hexdigest()[:10]
        chunks = create_text_chunks(page_text, source_name=f"web_{source_name}", page_num=1)
        
        for c in chunks:
            c["metadata"]["url"] = clean_target_url
            c["metadata"]["parent_url"] = clean_target_url
            c["metadata"]["type"] = "web"
            result["chunks"].append(c)

        base_url_for_join = clean_target_url.split("?")[0]
        if not base_url_for_join.endswith("/"):
            base_url_for_join += "/"

        valid_links = []
        for link in raw_links:
            full_link = urljoin(base_url_for_join, link).split("#")[0]
            if full_link.lower().endswith(".pdf"):
                continue
            link_parsed = urlparse(full_link)
            if link_parsed.netloc == base_domain and link_parsed.path.startswith(base_path_prefix):
                if not any(full_link.endswith(ext) for ext in [".zip", ".exe", ".iso", ".tar", ".gz"]):
                    if "flashsystem" in full_link.lower() or "sanvolumecontroller" in full_link.lower() or "san-volume-controller" in full_link.lower():
                        valid_links.append(full_link)
        
        result["links"] = list(set(valid_links))
        return result

    except Exception as e:
        result["error"] = str(e)
        return result

def parse_url(url: str, max_depth: int = 1, max_pages: int = 30, global_visited: set = None, global_hashes: set = None) -> List[Dict[str, Any]]:
    """
    抓取並解析技術文檔網址（支援 JS 渲染 SPA 頁面與目錄子章節頁面之同網域遞迴爬取）
    """
    if global_visited is None: global_visited = set()
    if global_hashes is None: global_hashes = set()
    
    url = url.strip()
    if not url or url.startswith("#"):
        return []

    visited_urls: Set[str] = set()
    all_chunks: List[Dict[str, Any]] = []

    base_parsed = urlparse(url)
    base_domain = base_parsed.netloc
    base_path_prefix = "/".join(base_parsed.path.rstrip("/").split("/")[:-1])

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    queue = [(url, 0)]

    print(f"🌐 啟動網頁動態爬蟲 (入口: {url}, 最大深度: {max_depth})")

    while queue and len(visited_urls) < max_pages:
        current_url, depth = queue.pop(0)
        clean_target_url = current_url.split("#")[0]
        
        if clean_target_url in visited_urls or clean_target_url in global_visited:
            continue
        
        visited_urls.add(clean_target_url)
        global_visited.add(clean_target_url)

        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                html_content = ""
                # 首先嘗試 HTTP GET
                response = httpx.get(clean_target_url, headers=headers, timeout=60000.0, follow_redirects=True)
                if response.status_code == 200:
                    html_content = response.text

                # 如果頁面過短或是 IBM Docs 等單頁前端 (SPA)，改用 Playwright 無頭瀏覽器渲染
                if len(html_content) < 2000 or "digitalData" in html_content or "ibm.com/docs" in clean_target_url:
                    rendered = fetch_rendered_html_with_playwright(clean_target_url)
                    if rendered and len(rendered) > 2000:
                        html_content = rendered
                    else:
                        raise Exception("Playwright 渲染失敗或返回空內容，觸發 Rollback")

                if not html_content:
                    break

                page_text, raw_links = extract_clean_page_content(html_content)
                
                content_hash = hashlib.md5(page_text.encode()).hexdigest()
                if content_hash in global_hashes:
                    print(f"  ├─ [內容重複] 已跳過相同的內容區塊 ({clean_target_url})")
                    break
                global_hashes.add(content_hash)
                
                source_name = hashlib.md5(clean_target_url.encode()).hexdigest()[:10]
                chunks = create_text_chunks(page_text, source_name=f"web_{source_name}", page_num=1)
                
                for c in chunks:
                    c["metadata"]["url"] = clean_target_url
                    c["metadata"]["parent_url"] = url
                    c["metadata"]["type"] = "web"
                    all_chunks.append(c)

                print(f"  ├─ [已解析 ({len(visited_urls)}/{max_pages})] {clean_target_url} ({len(chunks)} Chunks)")

                if depth < max_depth:
                    base_url_for_join = clean_target_url.split("?")[0]
                    if not base_url_for_join.endswith("/"):
                        base_url_for_join += "/"

                    for link in raw_links:
                        full_link = urljoin(base_url_for_join, link).split("#")[0]
                        
                        if full_link.lower().endswith(".pdf"):
                            download_pdf_safely(full_link)
                            continue
                            
                        link_parsed = urlparse(full_link)
                        if link_parsed.netloc == base_domain and link_parsed.path.startswith(base_path_prefix):
                            if not any(full_link.endswith(ext) for ext in [".zip", ".exe", ".iso", ".tar", ".gz"]):
                                if "flashsystem" in full_link.lower() or "sanvolumecontroller" in full_link.lower() or "san-volume-controller" in full_link.lower():
                                    if full_link not in visited_urls and full_link not in global_visited:
                                        queue.append((full_link, depth + 1))
                break # 成功處理，跳出重試迴圈
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    import time
                    wait_time = 2 ** attempt
                    print(f"  └─ [網路異常] 抓取失敗 ({e})，{wait_time} 秒後進行第 {attempt+2} 次重試...")
                    time.sleep(wait_time)
                else:
                    print(f"  └─ [嚴重警告] 頁面徹底失敗已放棄: {clean_target_url}")
                    try:
                        with open(config.RAW_DATA_DIR / "failed_urls.log", "a", encoding="utf-8") as f:
                            f.write(f"{clean_target_url}\n")
                    except Exception:
                        pass

    print(f"✅ 網頁目錄爬取完成！共處理 {len(visited_urls)} 個關聯頁面，生成 {len(all_chunks)} 個向量 Chunk。")
    return all_chunks

def download_pdf_safely(pdf_url: str):
    """安全地在背景下載 PDF，避免阻塞主線程"""
    try:
        import os
        import httpx
        import config
        file_name = pdf_url.split("/")[-1]
        if not file_name.lower().endswith('.pdf'):
            return
        save_path = config.RAW_PDF_DIR / file_name
        
        if save_path.exists():
            return
            
        print(f"  ├─ [PDF 攔截] 正在下載: {file_name} ...")
        response = httpx.get(pdf_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}, timeout=60000.0, follow_redirects=True)
        
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print("  ├─ [PDF 攔截] ✅ 下載完成")
        else:
            print(f"  ├─ [PDF 攔截] ❌ 下載失敗 (HTTP {response.status_code})")
    except Exception as e:
        print(f"  ├─ [PDF 攔截] ❌ 發生錯誤 ({e})")