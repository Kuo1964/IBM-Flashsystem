# 規格書 0003: 多使用者自動建檔認證、全量審計日誌與多輪對話防失焦系統

## Problem Statement

目前 IBM FlashSystem / SVC 專家系統採用全團隊共用 PIN 碼驗證，缺乏個別使用者的帳號隔離與對話歷程追蹤功能。若管理員需要手動為團隊 80 位同仁建立與維護帳號，將造成龐大的行政負擔。
此外，當同仁在同一個對話中連續提出多個不同主題的問題時，既有 RAG 系統容易因為前置問題的數萬字參考手冊累積疊加，導致大語言模型發生「注意力稀釋」與「跨主題上下文漂移 (Context Drift)」，造成後續問答失焦或產生混亂。

## Solution

1. **Auto-Provisioning 零負擔使用者認證體系**：
   - 同仁首次登入時輸入工號/姓名與自訂密碼，系統自動註冊建檔並核發 JWT Token，自動開闢該使用者的專屬會話空間。
2. **Audit Trail Engine 全量對話審計與計費追蹤**：
   - 以結構化 SQLite 資料庫 (`storage_audit.db`) 完整保存同仁問答歷程、官方手冊引用清單 (JSON)、Token 消耗、估算費用與耗時，並支援管理者匯出報表。
3. **Smart Context Isolation 智慧多輪防失焦引擎**：
   - 實施單輪 RAG 參考資料嚴格隔離機制：每一輪檢索出的 25 筆手冊資料僅在該輪生效，下一輪歷史 Prompt 僅攜帶問答純文字摘要；
   - 具備話題切換偵測與指代消解功能，追問時自動還原完整主語，換題時自動完全清空舊題手冊雜訊。
4. **ChatGPT 風格現代自適應雙欄介面**：
   - 前端提供可收合之歷史對話側邊欄（依時間分組）、一鍵開啟新對話按鈕與右上角使用者狀態卡片。

---

## User Stories

1. As an **儲存維運工程師 (Engineer)**, I want to log in using my employee ID / name and password without waiting for admin approval, so that I can immediately start asking FlashSystem / SVC questions.
2. As an **儲存維運工程師 (Engineer)**, I want my login state to be remembered across browser restarts, so that I do not need to re-enter my credentials every time.
3. As an **儲存維運工程師 (Engineer)**, I want to browse my past conversation topics in a sidebar, so that I can quickly review previous troubleshooting steps and CLI commands.
4. As an **儲存維運工程師 (Engineer)**, I want to click a "New Topic" button to start a fresh discussion, so that my new question is completely unpolluted by previous topic contexts.
5. As an **儲存維運工程師 (Engineer)**, I want to ask follow-up questions (e.g. "What are the exact CLI commands for that?") seamlessly, so that the AI understands the context while retrieving precise official manual snippets.
6. As an **儲存系統管理者 (Admin)**, I want all user queries, answers, cited manual pages, and token costs to be recorded in an audit database, so that I can perform operational auditing and expenditure analysis.
7. As an **儲存系統管理者 (Admin)**, I want to export team conversation audit logs to structured reports, so that I can share technical Q&A summaries with management.
8. As an **AI 專家系統大腦 (LLM Engine)**, I want prior RAG context chunks to be isolated and wiped when a user changes topics, so that my attention is 100% focused on the new storage question without hallucination.

---

## Implementation Decisions

### 1. 認證與授權架構 (`auth.py`)
- 採用 SQLite + HMAC-SHA256 密碼雜湊 + JWT Token 驗證。
- API 端點：
  - `POST /api/auth/login` (支援 Auto-Provisioning：若使用者不存在則自動建立)
  - `GET /api/auth/me` (驗證 Token 並取得使用者資訊與角色)
  - `POST /api/auth/logout`

### 2. 全量審計引擎 (`audit_logger.py`)
- SQLite 資料庫結構 (`storage_audit.db`)：
  - `users`: `user_id`, `username`, `password_hash`, `role`, `created_at`
  - `sessions`: `session_id`, `user_id`, `title`, `created_at`, `updated_at`
  - `chat_audit_logs`: `log_id`, `session_id`, `user_id`, `query_text`, `answer_text`, `sources_json`, `tokens_used`, `cost_estimate_usd`, `cost_estimate_twd`, `response_time_seconds`, `timestamp`
- 審計查詢 API：
  - `GET /api/sessions` (取得當前使用者之歷史對話清單)
  - `GET /api/sessions/{session_id}/messages` (取得特定會話歷史訊息)
  - `DELETE /api/sessions/{session_id}` (刪除對話)

### 3. 多輪對話防失焦與記憶管理 (`rag_core.py` / `query_rewriter.py`)
- **單輪 RAG 隔離規則**：
  在組裝發往 Gemini API 的對話歷史時，僅傳遞使用者的 `role: user` 與 `role: assistant` 純文字對話，**嚴禁將前幾輪的 `【IBM 官方參考資料】` 區塊納入歷史對話中**。
- **指代消解 (Coreference Resolution)**：
  若最新提問包含代詞（如「那指令呢」、「這個參數怎麼改」），透過輕量 Query Rewriter 結合最近 1 輪對話將提問還原為獨立完整的搜尋詞（如「NDVM 的遷移指令怎麼改」），再發起向量檢索。

### 4. 前端介面升級 (`static/index.html` / `portal_ui.html`)
- 採用自適應雙欄佈局：
  - 左側：可折疊歷史側邊欄（標題自動取自第 1 題摘要），含「➕ 開啟新主題」。
  - 中間：聊天串流主視窗。
  - 右上角：使用者頭像、名稱、工號與登出按鈕。

---

## Testing Decisions

1. **認證與自動建檔測試 (`tests/test_auto_provisioning_auth.py`)**：
   - 驗證首次登入自動註冊帳號成功並回傳 JWT Token。
   - 驗證密碼錯誤拒絕登入。
   - 驗證不同使用者之間的會話資料嚴格隔離。
2. **審計日誌完整性測試 (`tests/test_audit_logger.py`)**：
   - 驗證問答完成後，`chat_audit_logs` 完整寫入提問、解答、Sources JSON 與費用估算。
3. **多輪防失焦與 RAG 隔離測試 (`tests/test_multi_turn_anti_drift.py`)**：
   - 模擬情境：第 1 題問 NDVM ➔ 第 2 題問 MTU 9000。
   - 驗證第 2 題的 RAG 上下文完全不包含第 1 題的 NDVM 手冊，且輸出 100% 聚焦在 `chportethernet`。

---

## Out of Scope
- LDAP / Active Directory 企業網域集中認證（後續版本規劃）。
- 對話錄音與語音輸入轉文字 (STT) 功能。

## Further Notes
本功能將在獨立的 Git Worktree (`worktrees/user-auth-audit`) 進行完整原型與腳本驗證，驗收無誤後再無縫合併回主專案。
