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
    """解析 PDF 檔案，提取文字與技術圖表圖片"""
    doc = fitz.open(pdf_path)
    pdf_name = pdf_path.stem
    text_chunks = []
    image_records = []

    pdf_image_dir = config.EXTRACTED_IMAGES_DIR / pdf_name
    pdf_image_dir.mkdir(parents=True, exist_ok=True)

    for page_num in range(len(doc)):
        page = doc[page_num]
        actual_page = page_num + 1
        
        page_text = page.get_text("text")
        if page_text.strip():
            page_chunks = create_text_chunks(page_text, source_name=pdf_name, page_num=actual_page)
            text_chunks.extend(page_chunks)

        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                width, height = pil_img.size

                if width >= config.MIN_IMAGE_WIDTH and height >= config.MIN_IMAGE_HEIGHT:
                    img_filename = f"page_{actual_page}_img_{img_idx}.{image_ext}"
                    save_path = pdf_image_dir / img_filename
                    pil_img.save(save_path)

                    image_records.append({
                        "image_id": f"{pdf_name}_p{actual_page}_img{img_idx}",
                        "image_path": str(save_path),
                        "pdf_name": pdf_name,
                        "page_number": actual_page,
                        "width": width,
                        "height": height
                    })
            except Exception as e:
                print(f"[警告] 提取圖片失敗 (頁碼 {actual_page}, 圖片 {img_idx}): {e}")

    doc.close()
    return text_chunks, image_records

def fetch_rendered_html_with_playwright(url: str) -> str:
    """使用 Playwright 無頭瀏覽器渲染動態 JavaScript 網頁 (如 IBM Docs SPA)"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print(f"[警告] Playwright 渲染網頁失敗 ({url}): {e}")
        return ""

def extract_clean_page_content(html_content: str) -> Tuple[str, List[str]]:
    """從 HTML 內文中提取純文字與所有包含的超連結"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if href and not href.startswith(("#", "javascript:", "mailto:", "tel:")):
            links.append(href)

    for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
        element.decompose()

    clean_text = soup.get_text(separator="\n")
    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    full_text = "\n".join(lines)

    return full_text, links

def parse_url(url: str, max_depth: int = 1, max_pages: int = 30) -> List[Dict[str, Any]]:
    """
    抓取並解析技術文檔網址（支援 JS 渲染 SPA 頁面與目錄子章節頁面之同網域遞迴爬取）
    """
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
        
        if clean_target_url in visited_urls:
            continue
        
        visited_urls.add(clean_target_url)

        try:
            html_content = ""
            # 首先嘗試 HTTP GET
            response = httpx.get(clean_target_url, headers=headers, timeout=15.0, follow_redirects=True)
            if response.status_code == 200:
                html_content = response.text

            # 如果頁面過短或是 IBM Docs 等單頁前端 (SPA)，改用 Playwright 無頭瀏覽器渲染
            if len(html_content) < 2000 or "digitalData" in html_content or "ibm.com/docs" in clean_target_url:
                rendered = fetch_rendered_html_with_playwright(clean_target_url)
                if rendered:
                    html_content = rendered

            if not html_content:
                continue

            page_text, raw_links = extract_clean_page_content(html_content)
            
            source_name = hashlib.md5(clean_target_url.encode()).hexdigest()[:10]
            chunks = create_text_chunks(page_text, source_name=f"web_{source_name}", page_num=1)
            
            for c in chunks:
                c["metadata"]["url"] = clean_target_url
                c["metadata"]["parent_url"] = url
                c["metadata"]["type"] = "web"
                all_chunks.append(c)

            print(f"  ├─ [已解析 ({len(visited_urls)}/{max_pages})] {clean_target_url} ({len(chunks)} Chunks)")

            if depth < max_depth:
                for link in raw_links:
                    full_link = urljoin(clean_target_url, link).split("#")[0]
                    link_parsed = urlparse(full_link)
                    
                    if link_parsed.netloc == base_domain and link_parsed.path.startswith(base_path_prefix):
                        if not any(full_link.endswith(ext) for ext in [".zip", ".exe", ".iso", ".tar", ".gz"]):
                            if full_link not in visited_urls:
                                queue.append((full_link, depth + 1))

        except Exception as e:
            print(f"  └─ [警告] 抓取頁面失敗 ({clean_target_url}): {e}")

    print(f"✅ 網頁目錄爬取完成！共處理 {len(visited_urls)} 個關聯頁面，生成 {len(all_chunks)} 個向量 Chunk。")
    return all_chunks
