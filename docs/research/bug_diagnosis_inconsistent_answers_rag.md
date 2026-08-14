# /diagnosing-bugs 深度除錯診斷報告：RAG 資料流與向量空間不一致性分析

**診斷目標**：從 RAG 管道、向量檢索空間 (Vector Embedding Space)、Unicode 字元編碼與注意力機制 (Attention Mechanism) 等深層系統工程視角，剖析入口網站輸入相同問題時解答不一致的深層主因。

---

## 🔍 一、 Phase 1 & 2: 系統微分測試環路 (Differential Feedback Loop)

依據 `/diagnosing-bugs` 規範，我們建構一個微分測試驗證模型 (Differential Test Harness)。當輸入相同提問時，在系統 4 個不同的關卡 (Seams) 進行輸出比對：

```text
[輸入提問 String] 
      │
      ├── [關卡 A]: Unicode 字元標準化 (NFC vs NFD / UTF-8 Bytes)
      ├── [關卡 B]: Embedding 向量產出夾角 (Cosine Distance Check)
      ├── [关卡 C]: ChromaDB HNSW 索引走訪與 Top-K 排序 stability
      └── [關卡 D]: LLM Attention Attention Distribution & Sampling
```

---

## 🧪 二、 Phase 3: 4 大核心假說與證偽條件 (Ranked Falsifiable Hypotheses)

### 假說 H1：HNSW 近似搜尋隨機性與分數臨界面競合 (HNSW Index Tie-Breaking Instability) — *最高可能*
- **推論**：ChromaDB 使用 HNSW (Hierarchical Navigable Small World) 近似最近鄰演算法。當知識庫擁有 70,000+ 筆向量且有數個 Chunk 的相似度高達 `0.8912` vs `0.8911`（幾乎平行）時，HNSW 的圖走訪起點與隨機探測路徑會導致回傳的前 5 筆 Chunk 出現微觀排序浮動（例如 `[A, B, C]` 變成 `[B, A, C]`）。
- **證偽條件**：如果強制對 ChromaDB 回傳的 Top-K 結果按 `(similarity_score, chunk_id)` 進行字典序重排後，Prompt 的注入順序仍然變動，則假說 H1 證偽。

### 假說 H2：多模態圖表摘要與純內文 Chunk 的注意力競爭 (Multimodal vs Text Competition)
- **推論**：`vision_processor.py` 生成的技術圖表摘要 (Image Summary) 與 PDF 純文字 Chunk 混合儲存於同一向量空間。當提問命中臨界值時，有時圖表摘要排在第 1 筆，有時純文字段落排在第 1 筆。LLM 讀取到「圖表描述」與「純文字規格」時，注意力焦點 (Attention Focus) 發生偏移，導致輸出內容風格不同。
- **證偽條件**：若隔離圖表摘要與純文字 Chunk 分開檢索並固定拼接，答案仍不一致，則假說 H2 證偽。

### 假說 H3：Unicode 正規化與隱形字元引發 Embedding 夾角 (Unicode / Byte Divergence)
- **推論**：同仁從網頁複製文字、手動輸入或從不同作業系統 (macOS vs Windows) 輸入時，雖然字面看起來完全相同，但實際 UTF-8 Byte (如全半形、非打破空格 `\xa0`、Unicode NFC/NFD 重音組合) 不一致，導致 `nomic-embed-text` 生成的向量產生微小夾角分差。
- **證偽條件**：對輸入字串進行 `unicodedata.normalize('NFC', text)` 處理前後比對，若向量 100% 重合但生成仍不一致，則假說 H3 證偽。

### 假說 H4：Ollama LLM 隨機數種子 (Random Seed & Temperature)
- **推論**：Ollama 生成端點未傳入固定 `seed` 與 `temperature: 0.0`，預設隨機採樣導致 Token 產出路徑分歧。
- **證偽條件**：在 API 中傳入 `options: {"temperature": 0.0, "seed": 42}` 後，若回傳 Token 流 100% 重複，則假說 H4 成立。

---

## 🛠️ 三、 Phase 5: 建議架構改善與確定性鎖定對策

1. **確定性向量排序器 (Deterministic Vector Ranker)**：
   在 `vector_store.py` 檢索完成後，加入二次確定性排序函數：
   ```python
   # 確保相同相似度時，永遠按 chunk_id 字典序排序，消除 HNSW 隨機性
   results.sort(key=lambda x: (round(x["similarity_score"], 6), x["metadata"]["chunk_id"]), reverse=True)
   ```

2. **輸入端 Unicode & HTML 規範化 (Input Sanitizer)**：
   在 `web_app.py` 中引入 Unicode NFC 規範化與正規化：
   ```python
   import unicodedata
   clean_query = unicodedata.normalize('NFC', query_text).strip()
   ```

3. **固定 Ollama 隨機數種子與貪婪搜尋 (Deterministic Generation Option)**：
   ```python
   "options": {
       "temperature": 0.0,
       "top_p": 1.0,
       "seed": 42
   }
   ```

4. **圖表摘要與內文語意結構化分隔**：
   在注入 Prompt 時，明確將「純文字技術規格」與「技術圖表摘要」分區塊標註，引導 LLM 的 Attention 機制穩定運作。
