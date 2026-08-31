import json
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from parser import parse_single_page
from vector_store import add_chunks_to_db
import config

def worker_wrapper(url):
    return parse_single_page(url)

def run_test():
    visited_file = config.RAW_DATA_DIR / "global_visited_urls.json"
    hashes_file = config.RAW_DATA_DIR / "global_content_hashes.json"
    
    global_visited = set()
    global_hashes = set()
    
    if visited_file.exists():
        with open(visited_file) as f: global_visited = set(json.load(f))
    if hashes_file.exists():
        with open(hashes_file) as f: global_hashes = set(json.load(f))
        
    start_url = "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.3"
    queue = [start_url]
    
    print("🚀 發動驗證測試: 主從式單頁派發架構 (Max 5 pages)")
    
    pages_processed = 0
    max_pages = 5
    
    with ProcessPoolExecutor(max_workers=2) as executor:
        while queue and pages_processed < max_pages:
            batch = []
            while queue and len(batch) < 2:
                u = queue.pop(0)
                if u not in global_visited:
                    batch.append(u)
                    global_visited.add(u)
            
            if not batch:
                break
                
            futures = {executor.submit(worker_wrapper, u): u for u in batch}
            
            for future in as_completed(futures):
                u = futures[future]
                try:
                    res = future.result()
                    if res.get("error"):
                        print(f"  ❌ [{pages_processed+1}/{max_pages}] 失敗: {u} - {res['error']}")
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
                            
                        print(f"  ✅ [{pages_processed+1}/{max_pages}] 完成: {u} (過濾後寫入 {len(filtered)}/{len(chunks)} Chunks) (發現 {len(links)} 連結)")
                        
                        for l in links:
                            if l not in global_visited:
                                queue.append(l)
                                
                    pages_processed += 1
                    
                    # 即時 Checkpoint
                    with open(visited_file, "w") as f: json.dump(list(global_visited), f)
                    with open(hashes_file, "w") as f: json.dump(list(global_hashes), f)
                except Exception as e:
                    print(f"  ❌ [{pages_processed+1}/{max_pages}] 發生未預期錯誤: {u} - {e}")
                    pages_processed += 1
                
    print(f"✅ 測試完成！總共寫入 {len(global_visited)} 筆 URL 快取，{len(global_hashes)} 筆 Hash 紀錄。")

if __name__ == "__main__":
    run_test()
