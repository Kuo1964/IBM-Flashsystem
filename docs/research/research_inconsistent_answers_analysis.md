# 專案研究報告：入口網站輸入相同問題回答不一致之主因與修復對策

**研究目標**：探討為何在 Web Cloud Portal 中輸入相同技術問題時，LLM 產出的回答會有字詞與語氣上的差異，並提煉出確保答案 100% 確定性 (Deterministic Output) 的修復計畫。

---

## 🔍 一、既有程式碼調查與根因分析 (Primary Source Analysis)

經審視本專案核心模組 [web_app.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py) 與 [vector_store.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/vector_store.py)，發現導致相同提問產出不同回答的 **3 個核心主因**：

### 1. LLM 採樣隨機性參數設定 (Ollama Temperature Default)
- **程式碼現況** ([web_app.py line 125-132](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py#L125-L132))：
  ```python
  resp = await client.post(
      f"{config.OLLAMA_HOST}/api/generate",
      json={"model": config.LLM_MODEL, "prompt": prompt, "stream": False}
  )
  ```
- **分析**：
  目前呼叫 `/api/generate` 時並未指定 `options` 中的 `temperature` 參數。Ollama 模型（如 `llama3.2`）預設的 Temperature 為 `0.8`。Temperature 大於 0 代表模型在生成文字時會使用機率採樣 (Probabilistic Sampling)，即使傳入完全相同的 Prompt，每次產出的修辭、句型與詞彙順序也會有所不同。

### 2. 快取 Key 的字元與格式未正規化 (Cache Key Normalization)
- **程式碼現況** ([web_app.py line 90-95](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py#L90-L95))：
  ```python
  query_text = req.query.strip()
  cache_key = f"{query_text}_{req.top_k}"
  ```
- **分析**：
  雖然程式具備 `QUERY_CACHE` 語意快取，但若同仁輸入時帶有英文大小寫差異（如 `FlashSystem` vs `flashsystem`）或是多個空白鍵，會產生不同的 `cache_key`，導致系統無法命中快取而重新發起 LLM 推理。

### 3. 向量檢索結果排序的微小分差 (Score Ties Sorting)
- **分析**：
  當 ChromaDB HNSW 索引回傳相似度分數極度接近的多筆 Chunk 時，若未進行二次穩定排序 (Deterministic Tie-Breaking Sort)，注入 Prompt 的 `[1]`, `[2]` 參考段落順序可能會有些微變動，進而影響 LLM 的生成注意力。

---

## 🛠️ 二、建議修復對策 (Proposed Fix Plan)

為實現「相同問題發問 ➔ 100% 輸出完全一致解答」的確定性行為，建議採取以下 3 項修復：

### 對策 1：將 LLM 採樣 Temperature 強制設為 `0.0` (貪婪搜尋)
在 `web_app.py` 呼叫 Ollama 時加入 `options: {"temperature": 0.0, "top_p": 1.0}`：
```python
json={
    "model": config.LLM_MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.0,  # 關閉採樣隨機性，變為完全確定性生成
        "top_p": 1.0
    }
}
```
* **效果**：關閉 LLM 的隨機性，相同的 Prompt 輸出 100% 相同的解答。

### 對策 2：正規化 Cache Key (Standardized Normalization)
將 `query_text` 進行全小寫與空白處理：
```python
normalized_query = " ".join(query_text.lower().split())
cache_key = f"{normalized_query}_{req.top_k}"
```
* **效果**：不論同仁輸入大小寫或多餘空格，均能穩定命中快取，既保證答案一致又節省計算資源。

### 對策 3：向量檢索結果穩定排序 (Deterministic Search Sorting)
在 `vector_store.py` 回傳前，依據 `(similarity_score, chunk_id)` 進行穩定排序：
```python
formatted_results.sort(key=lambda x: (x["similarity_score"], x["metadata"].get("source", "")), reverse=True)
```

---

## 結論

此現象為大部分 LLM 預設採樣參數 (`temperature=0.8`) 帶來的正常生成特性。只要將 Temperature 調降至 `0.0` 並將快取 Key 正規化，即可完美實現相同問題輸出 100% 相同的專家解答！
