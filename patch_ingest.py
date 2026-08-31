import re

with open("ingest.py", "r", encoding="utf-8") as f:
    content = f.read()

old_block = """    # 3. 進入發牌與回收的主迴圈
    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            while url_queue and pages_processed < max_pages:
                batch = []
                # 一次派發一批 URL 給 workers
                while url_queue and len(batch) < workers:
                    u = url_queue.pop(0)
                    if u not in global_visited:
                        batch.append(u)
                        global_visited.add(u) # 立即標記為已拜訪，避免重複派發
                
                if not batch:
                    continue
                    
                futures = {executor.submit(_worker_wrapper, u): u for u in batch}
                
                for future in as_completed(futures):
                    u = futures[future]
                    try:
                        res = future.result()
                        if res.get("error"):
                            print(f"  ❌ 抓取失敗: {u} ({res['error']})")
                        else:
                            chunks = res.get("chunks", [])
                            links = res.get("links", [])
                            
                            # 主進程去重 (Cross-worker filtering)
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
                                
                                # 更新 manifest 以支援後續的源碼管理
                                source_name = filtered[0]["metadata"]["source"]
                                manifest[source_name] = {
                                    "type": "web",
                                    "url": u,
                                    "chunks": len(filtered)
                                }
                                
                            print(f"  ├─ [已解析] {u} (過濾後寫入 {len(filtered)}/{len(chunks)} Chunks) (發現 {len(links)} 新連結)")
                            
                            # 將新發現的子連結加入佇列
                            new_links_added = 0
                            for l in links:
                                if l not in global_visited and l not in url_queue:
                                    url_queue.append(l)
                                    new_links_added += 1
                                    
                        pages_processed += 1
                        
                        # 【即時檢查點 Checkpoint】每完成一頁立刻儲存狀態
                        with open(visited_file, "w") as f: json.dump(list(global_visited), f)
                        with open(hashes_file, "w") as f: json.dump(list(global_hashes), f)
                        with open(queue_file, "w") as f: json.dump(url_queue, f)
                        with open(manifest_path, "w", encoding="utf-8") as f: json.dump(manifest, f, indent=4)

                    except Exception as e:
                        if u in global_visited:
                            global_visited.remove(u)
                        print(f"  ❌ 發生未預期錯誤: {u} - {e}")
    except KeyboardInterrupt:"""

def get_inner_logic(u_var, res_var):
    return f"""                    if {res_var}.get("error"):
                        print(f"  ❌ 抓取失敗: {{{u_var}}} ({{{res_var}['error']}})")
                    else:
                        chunks = {res_var}.get("chunks", [])
                        links = {res_var}.get("links", [])
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
                            manifest[source_name] = {{"type": "web", "url": {u_var}, "chunks": len(filtered)}}
                        print(f"  ├─ [已解析] {{{u_var}}} (過濾後寫入 {{len(filtered)}}/{{len(chunks)}} Chunks) (發現 {{len(links)}} 新連結)")
                        for l in links:
                            if l not in global_visited and l not in url_queue:
                                url_queue.append(l)
                    pages_processed += 1
                    with open(visited_file, "w") as f: json.dump(list(global_visited), f)
                    with open(hashes_file, "w") as f: json.dump(list(global_hashes), f)
                    with open(queue_file, "w") as f: json.dump(url_queue, f)
                    with open(manifest_path, "w", encoding="utf-8") as f: json.dump(manifest, f, indent=4)"""

new_block = f"""    # 3. 進入發牌與回收的主迴圈
    try:
        if workers == 1:
            while url_queue and pages_processed < max_pages:
                u = url_queue.pop(0)
                if u in global_visited:
                    continue
                global_visited.add(u)
                try:
                    res = _worker_wrapper(u)
{get_inner_logic("u", "res")}
                except Exception as e:
                    if u in global_visited: global_visited.remove(u)
                    print(f"  ❌ 發生未預期錯誤: {{u}} - {{e}}")
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                while url_queue and pages_processed < max_pages:
                    batch = []
                    while url_queue and len(batch) < workers:
                        u = url_queue.pop(0)
                        if u not in global_visited:
                            batch.append(u)
                            global_visited.add(u)
                    if not batch: continue
                    futures = {{executor.submit(_worker_wrapper, u): u for u in batch}}
                    for future in as_completed(futures):
                        u = futures[future]
                        try:
                            res = future.result()
{get_inner_logic("u", "res")}
                        except Exception as e:
                            if u in global_visited: global_visited.remove(u)
                            print(f"  ❌ 發生未預期錯誤: {{u}} - {{e}}")
    except KeyboardInterrupt:"""

content = content.replace(old_block, new_block)

with open("ingest.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Patched ingest.py successfully.")
