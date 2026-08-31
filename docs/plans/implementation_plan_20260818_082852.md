# Implementation Plan - IBM FlashSystem 企業級 AI 智慧技術客服與服務台系統

**建立時間**: `2026-08-18 08:28:52`  
**分支名稱**: `feature/enterprise-customer-service-portal`  
**核心目標**: 將知識庫檢索入口全面升級為「企業級 AI 智慧技術客服系統 (Technical Service Desk)」，具備 4 階意圖智慧分流、多輪會話隔離與意圖重寫、目錄頁 TOC 去噪過濾、以及現代化對話客服介面。

---

## 🗺️ 系統模組與資料流 (Context Map)

```mermaid
graph TD
    User[客戶/工程師] --> UI[前端客服介面 static/index.html]
    UI -->|帶 session_id 與歷史清單| WebApp[web_app.py 會話管理]
    WebApp --> SessionMgr[Session Manager 記憶體會話快取]
    SessionMgr --> QueryCondenser[多輪追問意圖重寫器]
    QueryCondenser --> RAGCore[rag_core.py 4階意圖分流引擎]
    
    RAGCore --> VecStore[vector_store.py 目錄頁過濾與純 SQLite 檢索]
    VecStore --> CleanChunks[純淨實體技術正文 Chunks]
    
    RAGCore --> Router{4階意圖分流}
    Router -->|Tier 1: 快速指令| FastTrack[單次極速直答 3~5s (置頂指令碼/一鍵複製)]
    Router -->|Tier 2: 規格諮詢| SpecCard[規格參數卡片 3~5s]
    Router -->|Tier 3: 故障排查| TroubleShoot[引導式排查步驟 5~8s]
    Router -->|Tier 4: 架構遷移| LongChain[並行分章節鏈式生成 20s (萬字指南)]
    
    FastTrack & SpecCard & TroubleShoot & LongChain --> FinalAns[100% 純淨精準回答]
    FinalAns --> UI
```

---

## 🛠️ 分階段實作計畫 (Implementation Tasks)

### 階段一：後端核心純淨化與 4 階意圖分流
1. **[MODIFY] `prompts.py`**：
   - 徹底移除任何寫死的業務專有名詞（如 PBR, Volume Group, lsvolumegroupreplication 等）。
   - 建立 4 套專業客服動態 Prompt 樣板（指令直答、規格卡片、故障排查、架構指南）。
2. **[MODIFY] `vector_store.py`**：
   - 實作目錄頁 (`TOC`) 自動偵測過濾器（過濾點線 `.... 510` 等無效切片）。
   - 加入專有名詞複合加權（對 `service IP`、`satask` 等運維詞彙精準提權）。
3. **[MODIFY] `rag_core.py`**：
   - 實作 4 階意圖智慧分類器（自動識別是指令查詢、規格諮詢、故障排查或長篇架構專案）。
   - 指令查詢走 Tier 1 極速直答通道；大型專案才走 Tier 4 鏈式管線。

### 階段二：Session 會話管理與多輪追問防污染
1. **[MODIFY] `web_app.py`**：
   - 擴充 `/api/query` 支援 `session_id` 與多輪對話訊息。
   - 新增 `/api/sessions/new` 與 `/api/sessions/clear` 介面。
2. **[MODIFY] `rag_core.py`**：
   - 實作 `condense_followup_query` 輕量多輪意圖重寫器。

### 階段三：現代化客服前端介面升級
1. **[MODIFY] `static/index.html`**：
   - 建立左側客服側邊欄（「➕ 開新對話」、「歷史會話清單」、「工單匯出」）。
   - 對話區域重構為**現代化對話氣泡 (Chat Stream UI)**。
   - 所有代碼區塊右上角加入「📋 一鍵複製」按鈕。
   - 參考資料升級為可折疊客服卡片。

---

## 🧪 驗證計畫 (Verification Matrix)

1. **指令查詢測試 (Tier 1)**：
   - 查詢「`我想用 command line 修改 service IP`」，驗證 3~5 秒內精準給出 `satask chserviceip` 指令，零無關章節。
2. **多輪追問測試**：
   - 第一題「`FlashSystem 9500 的連接埠`」，第二題「`那它的快取呢？`」，驗證成功精準回答快取容量，不被上一題舊切片污染。
3. **萬字長文測試 (Tier 4)**：
   - 查詢「`從傳統 GMCV 轉換成 PBR 詳細流程`」，驗證 25 秒內輸出完整三大章節與全套 CLI。
4. **Cloudflare 壓力驗證**：
   - 透過公網 URL 進行多輪對話，確保連線 100% 穩定。
