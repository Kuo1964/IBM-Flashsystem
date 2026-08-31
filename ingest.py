import argparse
import os
import json
import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import config
from parser import parse_single_page
from vector_store import add_chunks_to_db, delete_source_from_db

def _worker_wrapper(url: str):
    """將單一網頁解析任務包裝給 ProcessPoolExecutor"""
    try:
        return parse_single_page(url)
    except Exception as e:
        return {"url": url, "error": str(e)}

def run_ingestion(mode: str = "all", force: bool = False, max_depth: int = 50, max_pages: int = 5000, workers: int = 4):
    """
    增量掃描主程式 (Master-Worker Checkpoint 架構)
    """
    print("=" * 60)
    print(f"🚀 開始執行 IBM FlashSystem 知識庫增量掃描作業 (模式: {mode}, 強制更新: {force})")
    print("=" * 60)

    # 1. 讀取或建立狀態
    manifest_path = config.LOCAL_DATA_DIR / "manifest.json"
    visited_file = config.RAW_DATA_DIR / "global_visited_urls.json"
    hashes_file = config.RAW_DATA_DIR / "global_content_hashes.json"
    queue_file = config.RAW_DATA_DIR / "global_url_queue.json"

    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    global_visited = set()
    global_hashes = set()
    url_queue = []

    if visited_file.exists():
        with open(visited_file) as f: global_visited = set(json.load(f))
    if hashes_file.exists():
        with open(hashes_file) as f: global_hashes = set(json.load(f))
    if queue_file.exists():
        with open(queue_file) as f: url_queue = json.load(f)

    # 2. 準備初始 URL 佇列
    seed_urls = []
    if mode in ["url", "all", "url-only"]:
        url_list_path = config.RAW_DATA_DIR / "web_urls.txt"
        if url_list_path.exists():
            with open(url_list_path, "r", encoding="utf-8") as f:
                seed_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    # 如果這是全新的開始，或者要求強制更新，則重新灌入 Seed URLs
    if not url_queue or force:
        # 當 force 為 True 時，如果只是想強制重掃全部，我們將 global_visited 清空
        if force:
            global_visited.clear()
            global_hashes.clear()
        
        for u in seed_urls:
            if u not in url_queue and u not in global_visited:
                url_queue.append(u)

    print(f"\n🌐 準備處理網址佇列 (待處理: {len(url_queue)} 個網址)，啟動 {workers} 個並行 Worker...")

    pages_processed = 0
    total_new_chunks = 0
    
    # 3. 進入發牌與回收的主迴圈
    try:
        if workers == 1:
            while url_queue and pages_processed < max_pages:
                u = url_queue.pop(0)
                if u in global_visited:
                    continue
                global_visited.add(u)
                try:
                    res = _worker_wrapper(u)
                    if res.get("error"):
                        if u in global_visited: global_visited.remove(u)
                        print(f"  ❌ 抓取失敗: {u} ({res['error']})")
                    else:
                        chunks = res.get("chunks", [])
                        links = res.get("links", [])
                        filtered = []
                        for c in chunks:
                            text = c.get("text", "")
                            h = hashlib.md5(text.encode()).hexdigest()
                            if h not in global_hashes:
                                global_hashes.add(h)
                                filtered.append(c)
                        if filtered:
                            add_chunks_to_db(filtered)
                            total_new_chunks += len(filtered)
                            source_name = filtered[0]["metadata"]["source"]
                            manifest[source_name] = {"type": "web", "url": u, "chunks": len(filtered)}
                        print(f"  ├─ [已解析] {u} (過濾後寫入 {len(filtered)}/{len(chunks)} Chunks) (發現 {len(links)} 新連結)")
                        for l in links:
                            if l not in global_visited and l not in url_queue:
                                url_queue.append(l)
                    pages_processed += 1
                    with open(visited_file, "w") as f: json.dump(list(global_visited), f)
                    with open(hashes_file, "w") as f: json.dump(list(global_hashes), f)
                    with open(queue_file, "w") as f: json.dump(url_queue, f)
                    with open(manifest_path, "w", encoding="utf-8") as f: json.dump(manifest, f, indent=4)
                except Exception as e:
                    if u in global_visited: global_visited.remove(u)
                    print(f"  ❌ 發生未預期錯誤: {u} - {e}")
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                while url_queue and pages_processed < max_pages:
                    batch = []
                    while url_queue and len(batch) < workers:
                        u = url_queue.pop(0)
                        if u not in global_visited:
                            batch.append(u)
                            global_visited.add(u)
                    if not batch:
                        continue
                    futures = {executor.submit(_worker_wrapper, u): u for u in batch}
                    for future in as_completed(futures):
                        u = futures[future]
                        try:
                            res = future.result()
                            if res.get("error"):
                                if u in global_visited: global_visited.remove(u)
                                print(f"  ❌ 抓取失敗: {u} ({res['error']})")
                            else:
                                chunks = res.get("chunks", [])
                                links = res.get("links", [])
                                filtered = []
                                for c in chunks:
                                    text = c.get("text", "")
                                    h = hashlib.md5(text.encode()).hexdigest()
                                    if h not in global_hashes:
                                        global_hashes.add(h)
                                        filtered.append(c)
                                if filtered:
                                    add_chunks_to_db(filtered)
                                    total_new_chunks += len(filtered)
                                    source_name = filtered[0]["metadata"]["source"]
                                    manifest[source_name] = {"type": "web", "url": u, "chunks": len(filtered)}
                                print(f"  ├─ [已解析] {u} (過濾後寫入 {len(filtered)}/{len(chunks)} Chunks) (發現 {len(links)} 新連結)")
                                for l in links:
                                    if l not in global_visited and l not in url_queue:
                                        url_queue.append(l)
                            pages_processed += 1
                            with open(visited_file, "w") as f: json.dump(list(global_visited), f)
                            with open(hashes_file, "w") as f: json.dump(list(global_hashes), f)
                            with open(queue_file, "w") as f: json.dump(url_queue, f)
                            with open(manifest_path, "w", encoding="utf-8") as f: json.dump(manifest, f, indent=4)
                        except Exception as e:
                            if u in global_visited: global_visited.remove(u)
                            print(f"  ❌ 發生未預期錯誤: {u} - {e}")
    except KeyboardInterrupt:
        print("\n⚠️ 偵測到中斷訊號 (Ctrl+C)！目前進度已安全儲存於快取檔，下次啟動將從中斷點接續。")
        
    print("=" * 60)
    print(f"✅ 增量更新作業完成！共處理 {pages_processed} 個網頁，寫入 {total_new_chunks} 個新 Chunks。")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IBM FlashSystem 知識庫增量掃描程式")
    parser.add_argument("--pdf-only", action="store_true", help="僅處理 raw_data/pdfs 中的 PDF 手冊")
    parser.add_argument("--url-only", action="store_true", help="僅處理 web_urls.txt 中的技術網址")
    parser.add_argument("--force", action="store_true", help="強制重新處理所有項目（忽略 manifest 雜湊）")
    parser.add_argument("--max-depth", type=int, default=50, help="網頁爬取的最大深度")
    parser.add_argument("--max-pages", type=int, default=5000, help="最多爬取的網頁數量")
    parser.add_argument("--workers", type=int, default=4, help="並行處理的 Worker 數量")
    
    args = parser.parse_args()
    
    mode = "all"
    if args.url_only: mode = "url"
    elif args.pdf_only: mode = "pdf"
    
    run_ingestion(
        mode=mode, 
        force=args.force, 
        max_depth=args.max_depth, 
        max_pages=args.max_pages,
        workers=args.workers
    )
