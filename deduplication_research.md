# 知識庫去重機制 (Deduplication) 技術分析報告

針對 IBM FlashSystem 專案中的大量重複性內容（例如 CMMVC 錯誤碼跨版本重複），本系統採用了多層級的去重機制以確保向量庫 (ChromaDB) 的純淨度與儲存效率。以下為具體的實作邏輯分析：

## 1. 去重的核心層級：Chunk 層級的「全球內容雜湊 (Global Content Hash)」
我們的去重**不僅僅是比對網頁 (URL)**，而是深入到**最小單位 (Chunk)** 進行跨網頁的「內容精確比對」。

### 實作細節 (`ingest.py`)
在爬蟲抓取一個網頁並將其切割成多個 Chunk 之後，在寫入向量庫之前，會執行以下防護邏輯：
```python
text = c.get("text", "")
h = hashlib.md5(text.encode()).hexdigest()
if h not in global_hashes:
    global_hashes.add(h)
    filtered.append(c)
```
1. **MD5 雜湊計算**：將每一個 Chunk 的「純文字內容」轉換為唯一的 MD5 雜湊值 (Hash)。
2. **全域比對**：將該雜湊值與 `global_content_hashes.json` (目前記憶體中的 `global_hashes` 集合) 進行比對。
3. **跨網頁剔除**：只要這個 MD5 存在（代表這段文字在之前的**任何網頁**中已經出現過），這個 Chunk 就會被直接拋棄，不會送進 Embedding 模型，也不會寫入資料庫。

### 實際案例 (CMMVC 錯誤碼)
正如您所觀察到的，許多 CLI 指令或 `CMMVC` 錯誤訊息在不同版本（例如 `8.5.0` 與 `8.6.0`）之間是完全相同的。
當爬蟲在日誌中顯示：
`├─ [已解析] ... (過濾後寫入 8/589 Chunks)`
這代表爬蟲從這個網頁切出了 589 個段落，但經過 MD5 嚴格比對後，發現其中 **581 個段落是跟先前版本完全重複的廢話**！因此系統只會把這 8 個「真正有差異、被更新過」的新知識點寫入資料庫。

## 2. 網址層級去重 (`global_visited_urls.json`)
為了避免爬蟲陷入死循環，我們在最外層也做了一層 URL 去重：
```python
if u not in global_visited:
    batch.append(u)
    global_visited.add(u)
```
如果一個特定的網址字串已經被處理過，它就不會再被放入解析佇列中。

## 3. ChromaDB 內建 ID 去重 (`vector_store.py`)
在寫入底層資料庫時，每一個 Chunk 都配有基於來源與流水號生成的唯一 `chunk_id`。ChromaDB 在呼叫 `collection.add(ids=ids, ...)` 時，若遇到相同的 ID 也會自動覆蓋或忽略，這是我們的最後一道保險。

## 總結
您的觀察非常精確。本系統的去重是**「Chunk 內容層級的跨網頁比對」**。這確保了不管 IBM 的手冊在多少個章節或版本中重複貼上同一段 CMMVC 錯誤訊息，我們的向量庫裡永遠只會保留**最純粹、不佔用重複 Token 的單一份知識實體**。
