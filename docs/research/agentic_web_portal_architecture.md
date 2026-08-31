# 架構研究報告：賦予 Cloudflare Web 客服系統「Antigravity 專家大腦」全套能力

## 🎯 核心願景與目標
將原本「封閉式純向量 RAG」的 Cloudflare Web 客服系統，升級為與本地 Antigravity 頂級專家大腦完全對齊的 **「Agentic Autonomous RAG 專家大腦」**，使其具備：
1. **自主聯網即時查證 (Live Search Grounding)**：當本地知識庫不足或僅命中目錄頁時，自動聯網查詢 IBM 原廠最新資料。
2. **多模態架構圖智能關聯 (Visual Topology Embedding)**：自動精確關聯硬體實體機匣與內部拓撲圖。
3. **雙層容錯與防幻覺對齊 (Deterministic & Fact Grounding)**：保持高精準度，零瞎猜，並具備即時引用能力。

---

## 🏛️ 架構升級方案評估

### 方案一：Gemini 原生 Google Search Grounding (推薦，架構最優雅、零額外維護)
Google Gemini 官方 API 原生支援 Search Grounding 工具。在後端呼叫 Gemini API 時，直接在 payload 中宣告啟用 `google_search` 工具：

```python
payload = {
    "contents": [{"parts": [{"text": master_prompt}]}],
    "tools": [{"google_search": {}}],  # 啟用 Google 官方即時搜尋 Grounding
    "generationConfig": {
        "temperature": 0.1,
        "maxOutputTokens": 8192
    }
}
```

* **運作機制**：
  1. 後端將本地 ChromaDB 檢索到的技術上下文傳給 Gemini。
  2. 若本地 Context 充足（如一般的 FS5200 配置），Gemini 優先以本地 Context 回答。
  3. 若本地 Context 缺少詳細說明（例如罕見的 `CMMVC8000E` 僅有目錄連結），Gemini 會**自動發動 Google 搜尋檢索 IBM 官網即時內容**，並在回答中自動附上引用來源。
* **優點**：
  * 無需自己架設搜尋爬蟲或付費第三方 Search API。
  * 毫秒級自動銜接，反應迅速。
  * 100% 保持 Antigravity 專家的即時聯網查證能力。

---

### 方案二：自主 Tool-Use Agentic 循環 (ReAct 雙階段架構)
在 `rag_core.py` 中建立輕量級 Agent 決策環：
1. **Step 1 (Local Retrieval)**：先查 ChromaDB。
2. **Step 2 (Confidence Evaluation)**：若 Chunks 內容過短、全為目錄連結或相似度低於門檻，判定為「知識庫未完全收錄」。
3. **Step 3 (Live Fallback Search)**：呼叫專屬的 IBM Docs API 或搜尋模組，精準抓取 `https://www.ibm.com/docs/en/...` 頁面內文。
4. **Step 4 (Final Synthesis)**：結合本地資料與聯網資料進行結構化生成。

---

## 🚀 實施步驟藍圖 (Implementation Roadmap)

1. **升級 `rag_core.py`**：
   * 在 `_call_gemini_api` 加入 `tools: [{"google_search": {}}]` 支援。
   * 解析並保留 Gemini 返回的 groundingMetadata 與即時引用網址。
2. **更新提示詞與系統真理**：
   * 在 `prompts.py` 中引導大模型：「當本地資料僅為目錄代碼而無詳細故障排除步驟時，主動以原廠官方搜尋檢索該錯誤代碼之具體定義與修復指引」。
3. **重啟 Web 常駐守護進程**：
   * 透過 `start_portal_daemon.py` 更新上線。

