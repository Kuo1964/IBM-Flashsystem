# 【分支測試】IBM FlashSystem Web Portal RAG 品質與解答結構優化計畫

**分支名稱**: `feature/rag-quality-upgrade`  
**時間戳記**: `2026-08-14 15:48:13`

本計畫旨在分支 `feature/rag-quality-upgrade` 上重構 Web 雲端問答入口的 RAG 檢索邏輯與 Prompt 生成機制，讓 Web 網站入口產出**與 CLI/Agent 詢問完全相同品質、結構嚴謹且具備專用指令的解答**，同時修復前端圖片預覽空白 Bug 與低相關噪訊。

---

## 🎯 測試目標與四大重構模組

1. **相似度過濾與噪訊剔除 (Similarity Threshold Cutoff >= 75%)**：
   - 設定相似度門檻，低於 75% 的不相關圖表或段落直接過濾，解決「引述無關 Fibre Channel GUI 圖表」問題。
2. **純文字優先與 Context 擴充 (Top-K=10 Text-First RAG)**：
   - 擴充檢索深度至 `top_k=10`，優先提供高相關的純文字技術規範，讓 LLM 掌握完整跨頁脈絡（如 GMCV 轉 PBR 之完整步驟）。
3. **專家級 Prompt 結構化輸出範本 (Expert Structured Prompt)**：
   - 引入資深儲存專家 Persona，要求解答必須強制包含：
     - **⚠️ 轉換前關鍵注意事項與前置條件**
     - **📋 詳細轉換步驟流程 (GUI 操作 + CLI 具體命令)**
     - **🔍 轉換後驗證與監控指令**
4. **確定性參數與圖片預覽修復 (Deterministic Output & Lightbox Fix)**：
   - 設定 `temperature: 0.0` 與 `seed: 42` 鎖定回答恆定性。
   - 修復前端圖片 URL 拼接雙斜線 Bug (`/api/images//Users/...`)，讓技術圖表彈窗能夠真實顯示。

---

## 🛠️ 擬變更檔案清單 (Proposed Changes)

### [MODIFY] [vector_store.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/vector_store.py)
- `query_kb()` 新增 `min_similarity=0.75` 參數過濾低分噪訊。
- 增加按 `(similarity_score, chunk_id)` 字典序的確定性二次排序。

### [MODIFY] [web_app.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py)
- 重構 `prompt` 模板，導入資深 FlashSystem 儲存專家結構化輸出規範。
- 將預設檢索深度調至 `top_k=8`~`10`。
- 在 Ollama `/api/generate` 請求中加入 `options: {"temperature": 0.0, "seed": 42}` 鎖定確定性輸出。
- 修復 `/api/images/{image_path}` 路由，相容絕對與相對圖片路徑，徹底解決圖片彈窗空白 Bug。

### [MODIFY] [static/index.html](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/static/index.html)
- 修復 `openImageModal(path)` 圖片網址路徑編碼，支援正確顯示預覽圖。
- 於引述卡片上標註具體圖片檔名（如 `page_264_img_0`），消除重複標籤疑慮。

---

## 🔬 驗證與測試計畫 (Verification Plan)

### 1. 差異對比測試 (Differential Comparison)
- 輸入測試問題：`如何將 GMCV 轉換至 PBR？`
- **預期效果**：Web 入口產出包含 **⚠️ 轉換前注意事項、📋 4 大步驟流程與 CLI 命令、🔍 驗證指令** 的完整專業解答。

### 2. 噪訊與圖片預覽測試
- 點擊技術圖表預覽按鈕，驗證圖片 Modal 彈窗可正常載入顯示實體圖檔。
- 確認低於 75% 相似度的不相干圖表不會被強行引述。
