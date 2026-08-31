"""
IBM FlashSystem 專家系統 - 增量更新與資料吞吐管道 (Ingestion Pipeline)
比對 manifest.json 中的檔案 Hash 值，自動對新增或修改的文件與圖片進行增量向量化處理
"""

import json
from pathlib import Path
from typing import Dict, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from parser import parse_pdf, parse_url, calculate_file_hash
from vision_processor import generate_image_summary
from vector_store import add_chunks_to_db, delete_source_from_db

def load_manifest() -> Dict[str, Any]:
    """載入增量記錄檔 manifest.json"""
    if config.MANIFEST_FILE.exists():
        try:
            with open(config.MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[警告] 讀取 manifest.json 失敗: {e}")
    return {}

def save_manifest(manifest: Dict[str, Any]):
    """儲存增量記錄檔 manifest.json"""
    with open(config.MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def load_global_set(file_path: Path) -> set:
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_global_set(file_path: Path, data_set: set):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(list(data_set), f, ensure_ascii=False)
    except Exception as e:
        print(f"[警告] 無法儲存全域狀態檔 {file_path.name}: {e}")

import multiprocessing as mp

def _pdf_worker(pdf_path_str: str, queue: mp.Queue):
    """獨立子進程工作者：執行 PDF 解析與圖片生成，避免 C 庫崩潰波及主程式"""
    try:
        from pathlib import Path
        from parser import parse_pdf
        from vision_processor import generate_image_summary

        pdf_path = Path(pdf_path_str)
        text_chunks, image_records = parse_pdf(pdf_path)

        all_chunks = list(text_chunks)
        for img_rec in image_records:
            try:
                img_chunk = generate_image_summary(img_rec)
                if img_chunk:
                    all_chunks.append(img_chunk)
            except Exception:
                continue

        queue.put({
            "status": "success",
            "chunks": all_chunks,
            "images_count": len(image_records)
        })
    except Exception as e:
        queue.put({
            "status": "error",
            "error": str(e)
        })

def process_single_pdf_isolated(pdf_path: Path) -> Dict[str, Any]:
    """使用完全隔離的 spawn 子進程解析 PDF，阻斷任何底層 Segfault"""
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    proc = ctx.Process(target=_pdf_worker, args=(str(pdf_path), queue))
    proc.start()
    proc.join(timeout=1800)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"status": "timeout", "error": "處理逾時 (超過 1800 秒)"}

    if proc.exitcode != 0:
        return {"status": "crash", "error": f"底層 C 庫異常退出 (ExitCode: {proc.exitcode})，已成功防護隔離"}

    if not queue.empty():
        return queue.get()
    return {"status": "error", "error": "子進程未回傳結果"}

def _url_worker(url: str, max_depth: int, max_pages: int, global_visited_list: list, global_hashes_list: list, queue: mp.Queue):
    """獨立子進程網頁爬蟲工作者：隔離 Playwright Node.js IPC 管道，徹底杜絕 Segfault"""
    try:
        from parser import parse_url
        g_visited = set(global_visited_list)
        g_hashes = set(global_hashes_list)
        web_chunks = parse_url(url, max_depth=max_depth, max_pages=max_pages, global_visited=g_visited, global_hashes=g_hashes)
        queue.put({
            "status": "success",
            "chunks": web_chunks,
            "visited": list(g_visited),
            "hashes": list(g_hashes)
        })
    except Exception as e:
        queue.put({
            "status": "error",
            "error": str(e)
        })

def process_single_url_isolated(url: str, max_depth: int, max_pages: int, global_urls: set, global_hashes: set) -> Dict[str, Any]:
    """使用完全隔離的 spawn 子進程抓取網頁，阻斷任何 Node.js EPIPE / Segfault"""
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    proc = ctx.Process(target=_url_worker, args=(url, max_depth, max_pages, list(global_urls), list(global_hashes), queue))
    proc.start()
    proc.join(timeout=1800)  # 30 分鐘防護逾時

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"status": "timeout", "error": "網頁爬取逾時 (超過 1800 秒)"}

    if proc.exitcode != 0:
        return {"status": "crash", "error": f"底層 Node/C 異常退出 (ExitCode: {proc.exitcode})，已成功防護隔離"}

    if not queue.empty():
        return queue.get()
    return {"status": "error", "error": "子進程未回傳結果"}

def run_ingestion(force_url: bool = False, max_depth: int = 50, max_pages: int = 5000):
    """執行全自動增量掃描與資料更新 (具備子進程隔離與深度防護)"""
    print("=" * 60)
    print(f"🚀 開始執行 IBM FlashSystem 知識庫增量掃描與更新作業 (安全隔離模式啟動)")
    print("=" * 60)

    manifest = load_manifest()
    updated_count = 0

    # 1. 處理 PDF 紅皮書
    pdf_files = list(config.RAW_PDF_DIR.glob("*.pdf")) + list(config.RAW_PDF_DIR.glob("*.PDF"))
    print(f"[資訊] 掃描到 {len(pdf_files)} 個 PDF 檔案。")

    for pdf_path in pdf_files:
        file_stem = pdf_path.stem
        file_hash = calculate_file_hash(pdf_path)

        # 檢查 Hash 是否變更
        if manifest.get(file_stem, {}).get("hash") == file_hash:
            print(f"  [跳過] 檔案未變更: {pdf_path.name}")
            continue

        print(f"\n📂 正在處理 PDF: {pdf_path.name} (隔離保護中) ...")
        
        # 使用隔離子進程處理
        result = process_single_pdf_isolated(pdf_path)
        
        if result.get("status") != "success":
            print(f"  [警告] 解析 {pdf_path.name} 遇到異常: {result.get('error')}，已自動跳過保護。")
            continue

        all_chunks = result.get("chunks", [])
        images_count = result.get("images_count", 0)

        # 清除舊記錄並寫入新記錄
        delete_source_from_db(file_stem)
        add_chunks_to_db(all_chunks)

        # 更新 Manifest
        manifest[file_stem] = {
            "type": "pdf",
            "filename": pdf_path.name,
            "hash": file_hash,
            "chunks_count": len(all_chunks),
            "images_count": images_count
        }
        updated_count += 1

    # 2. 處理網頁 URLs
    if config.RAW_URLS_FILE.exists():
        with open(config.RAW_URLS_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        print(f"\n🌐 掃描到 {len(urls)} 個技術文檔網址。")
        global_urls = load_global_set(config.GLOBAL_VISITED_URLS_FILE)
        global_hashes = load_global_set(config.GLOBAL_CONTENT_HASHES_FILE)
        
        try:
            for url in urls:
                url_key = f"url_{url}"
                url_hash = calculate_file_hash_text(url)

                if not force_url and manifest.get(url_key, {}).get("hash") == url_hash:
                    print(f"  [跳過] 網址未變更: {url}")
                    continue

                print(f"  🌐 正在啟動隔離進程抓取: {url} (Depth={max_depth}, MaxPages={max_pages}) ...")
                res = process_single_url_isolated(url, max_depth, max_pages, global_urls, global_hashes)
                
                if res.get("status") == "success":
                    web_chunks = res.get("chunks", [])
                    global_urls.update(res.get("visited", []))
                    global_hashes.update(res.get("hashes", []))

                    if web_chunks:
                        delete_source_from_db(web_chunks[0]["metadata"]["source"])
                        add_chunks_to_db(web_chunks)

                        manifest[url_key] = {
                            "type": "url",
                            "url": url,
                            "hash": url_hash,
                            "chunks_count": len(web_chunks)
                        }
                        updated_count += 1
                else:
                    print(f"  [警告] 網址處理失敗 ({url}): {res.get('error')}，已自動保護跳過。")
        finally:
            save_global_set(config.GLOBAL_VISITED_URLS_FILE, global_urls)
            save_global_set(config.GLOBAL_CONTENT_HASHES_FILE, global_hashes)

    # 儲存更新後的 Manifest
    save_manifest(manifest)

    print("\n" + "=" * 60)
    print(f"✅ 增量更新作業完成！共更新 {updated_count} 個項目。")
    print("=" * 60)

def calculate_file_hash_text(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()

if __name__ == "__main__":
    run_ingestion()
