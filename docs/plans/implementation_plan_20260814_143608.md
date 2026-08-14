# IBM FlashSystem 雲端問答入口 (Web Cloud Portal) 與 Wizard 部署建構計畫

**時間戳記**: `2026-08-14 14:36:08`

本計畫旨在為團隊同仁建立一個**高質感、極致體驗的雲端問答檢索 Web Portal (雲端知識入口)**，讓同事能直接透過網頁介面發問、搜尋 48 本 IBM FlashSystem 紅皮書與 70,000+ 筆向量技術文檔，並即時預覽技術圖表。同時透過 `wizard_cloud_setup.sh` 自動化 Bash 腳本，引導管理員在一分鐘內完成雲端部署與環境配置。

---

## 🗺️ Codebase Recon & Context Map (現況勘查與脈絡地圖)

### 既有架構與組件現況
- **config.py**: 設定 Ollama API 位址、模型名稱、本地隔離向量庫路徑。
- **vector_store.py**: 管理 ChromaDB 持久化向量庫，支援 50 筆小批次寫入與自動重試。
- **parser.py** + **vision_processor.py**: PDF 內文/圖表提取與 Playwright 無頭瀏覽器網頁爬蟲。
- **mcp_server.py**: 供 Antigravity / Claude Desktop 調用之 MCP Tool 服務。

### 新增網頁雲端入口架構 (Web Cloud Portal Architecture)

```text
[同事瀏覽器 (Browser Client)]
       │ (HTTP GET/POST / Chat UI)
       ▼
[web_app.py (FastAPI Web Portal & REST API Server)]
       ├── 靜態資源 (static/index.html) — 現代 Glassmorphism 視覺化 UI
       ├── /api/query 端點 ───► 呼叫 vector_store.py 檢索 + Ollama 生成答案
       ├── /api/stats 端點 ───► 讀取 manifest.json 與 ChromaDB 狀態
       └── /api/images/{path} ─► 提供 PDF 提取圖表安全預覽
       
[wizard_cloud_setup.sh (Wizard 一鍵部署與環境設定嚮導)]
       └── 引導管理員/同事配置網域、Port、Ollama Host 與啟動服務
```

---

## 🛡️ Guardrail Spec (防護規格與安全邊界)

1. **路徑穿越安全防護 (Path Traversal Protection)**：
   - 對 `/api/images/{image_path}` 靜態圖檔存取點進行嚴格驗證。
   - 使用 `Path(image_path).resolve().is_relative_to(config.LOCAL_DATA_DIR)` 檢查，禁止存取系統任何敏感目錄。
2. **併發與資源防護 (Concurrency & Rate Limiting)**：
   - 為防止多位同仁同時發問導致 Ollama/顯示卡負載過高，在 FastAPI 中建立 `asyncio.Semaphore(3)`，限制最多同時 3 筆 RAG 推理。
3. **服務降級機制 (Graceful Degradation)**：
   - 若呼叫 Ollama LLM 逾時 (Timeout > 30s)，自動降級回傳「最相關的 5 筆段落、頁碼與圖表連結」，保證 Web 介面永不掛掉。
4. **輸入字元過濾 (Input Sanitation)**：
   - 限制使用者查詢字數（最大 500 字元），過濾潛在 Prompt Injection 惡意字串。

---

## 🔍 Brownfield Diff Review (既有程式碼影響評估)

- **無破壞性變更 (Zero Breaking Changes)**：
  - 核心組件 `vector_store.py`, `ingest.py`, `parser.py`, `mcp_server.py` 均保持現狀，不修改內部演算法。
  - `config.py` 僅追加 `PORTAL_PORT = 8000` 與 `SERVER_HOST = "0.0.0.0"`，預設值保持向下相容。
  - 新增之 `web_app.py` 與 `wizard_cloud_setup.sh` 獨立運作，可與 `mcp_server.py` 同時並行。

---

## 🛠️ 導入步驟與模組設計 (Proposed Changes)

### 階段 1：設定與 Web Portal REST API 伺服器
* 修改 `config.py` 新增 Web Portal 的 Host 與 Port 設定。
* 新增 `web_app.py` (FastAPI + REST API 服務)。

### 階段 2：雲端問答入口 Web 前端 (Glassmorphism Web UI)
* 新增 `static/index.html` (現代 Glassmorphism 風格問答對話與圖表彈窗)。

### 階段 3：Wizard 自動化部署與設定腳本
* 新增 `wizard_cloud_setup.sh` (互動式部署腳本)。

---

## 🔬 驗證與測試計畫 (Verification Plan)

### 自動化測試
1. 執行 `.venv/bin/python web_app.py` 測試啟動，驗證 `/api/stats` 與 `/api/query` 介面回應。
2. 測試圖檔安全邊界：發起跨目錄請求驗證系統正確回傳 403 Forbidden。

### 人工審查與驗證
1. 打開瀏覽器存取 `http://localhost:8000` 測試問答對話與圖表彈窗。
2. 執行 `bash wizard_cloud_setup.sh` 驗證部署嚮導流程。
