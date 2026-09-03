# 0002 - IBM FlashSystem / SVC 跨裝置 Agentic Web 專家系統規格書 (Spec)

## Problem Statement (問題陳述)
使用者（儲存架構師、現場工程師與團隊同仁）在機房或外出時，需要透過手機或外網電腦即時向 IBM FlashSystem 與 SVC 專家系統進行架構諮詢、故障診斷與 CLI 操作查詢。
現有的簡易 Web API（單輪 RAG）缺乏 Antigravity Agent 的 ReAct 多輪思考與接地性審計（Grounding Auditor）能力，導致輸出不穩定且易產生幻覺；而若直接暴露本地 IDE 執行環境，又會面臨指令注入攻擊、會話上下文混淆與並發存取風險。

## Solution (解決方案)
建置 **Agentic Storage Gateway** 與 **Cloudflare Mobile Portal**：
1. 前端提供適配手機與電腦的現代化 Glassmorphic 響應式 Web 介面，支援 SSE 即時串流打字、CLI 代碼一鍵複製與架構圖拓撲展開。
2. 後端提供 ReAct 多輪 Agentic 推理核心，整合 Gemini 3.7 Thinking 模型、本地 ChromaDB 向量檢索工具與 Grounding Auditor 審計校驗，確保輸出質量與 Antigravity IDE 專家會話 100% 一致。
3. 入口具備 PIN 碼存取防護（PIN Access Guard）、速率限制與獨立 Session 隔離，並透過 Cloudflare Tunnel 建立安全的 HTTPS 公網通道。

## User Stories (使用者故事)

1. 作為一名現場工程師，我想在手機瀏覽器上開啟專屬網址並輸入 PIN 碼登入，以便在機房現場隨時查詢 SVC 節點更換步驟。
2. 作為一名現場工程師，我想在提問後看到逐字打字的即時串流（Streaming）回應，以便快速掌握診斷進度，無需長時間面對空白等待。
3. 作為一名儲存管理員，我想在電腦瀏覽器上查詢 FlashSystem 儲存池拓撲與 FlashCore Module (FCM) 規格，以便獲得與在 Antigravity 專家系統內完全一致的精確答案。
4. 作為一名儲存管理員，我想點擊回答中的 FlashSystem 拓撲圖或架構圖展開大圖檢視，以便看清複雜的硬體連線與背板插槽細節。
5. 作為一名儲存維運人員，我想一鍵複製回答中的 `svctask swapnode` 或 `lsnodecanister` 等 CLI 指令，以便直接貼上至 PuTTY/SSH 終端機執行。
6. 作為一名團隊同仁，我想在手機關閉再重新開啟時無需重複輸入 PIN 碼，以便享有順暢的工作體驗。
7. 作為一名系統擁有者，我想限制外網未授權人員存取 API 端點，以保護我的 API 配額與本地伺服器安全。
8. 作為一名系統擁有者，我想確保同事在網頁上的提問不會執行任何本機檔案修改或終端機系統指令，以杜絕 Prompt Injection 安全威脅。
9. 作為一名系統擁有者，我想讓多位同事同時提問時各自擁有獨立的會話佇列，以便彼此的對話紀錄與上下文不會互相干擾。
10. 作為一名系統擁有者，我想透過單一指令一鍵啟動後端服務與 Cloudflare Tunnel，並自動取得手機可掃描的 QR Code 與 HTTPS 網址，以便快速提供同仁使用。

## Implementation Decisions (實作決策)

### 1. 介面與通訊協定契約 (API Contracts)
- **PIN 驗證端點 (`POST /api/auth/verify`)**：
  - 接收 `{ "pin": "string" }`。
  - 驗證成功回傳 `{ "status": "ok", "token": "jwt_or_session_token" }`，失敗回傳 HTTP 401。
- **Agentic 串流問答端點 (`POST /api/query/stream`)**：
  - 請求標頭需包含 `Authorization: Bearer <token>` 或自訂驗證 Header。
  - 請求本體包含 `query`、`session_id` 與可選之歷史對話。
  - 採用 `text/event-stream` (Server-Sent Events) 協定，依序推送：
    - `event: thinking` (Agent 推理與工具調用狀態，如「正在檢索 FS5200 架構文檔...」)
    - `event: content` (即時生成的 Markdown 內容區塊)
    - `event: grounding` (審計比對與引用來源資訊)
    - `event: done` (生成結束信號)

### 2. 推理引擎與沙盒控制 (Agentic Gateway & Sandbox)
- **ReAct 多輪工具循環**：模型在生成前可自主決定調用 `query_vector_store`、`get_topology_chart` 或 `verify_cli_command`。
- **嚴格唯讀沙盒**：引擎僅註冊檢索類工具，絕不掛載任何 Shell 執行或檔案寫入 Handler。
- **Grounding 審計機制**：在串流輸出前，對提及的型號（如 SV1/SV3/FS9500）、RAID 等級與 CLI 語法進行文檔比對校驗，徹底抑制幻覺。

### 3. 前端 UI/UX 規範 (Glassmorphic Mobile-First)
- **跨平台響應式佈局**：以 Mobile-First 設計，手機端採用底部貼齊之輸入區與虛擬鍵盤避讓；電腦端支援寬螢幕雙欄/單欄自適應。
- **元件庫與樣式**：採用語意化 HTML + 現代 CSS 變數，支援深色模式（Dark Mode）。
- **指令區塊**：所有 Code block 自動附加語法高亮與一鍵複製按鈕。

### 4. 部署與網路通道 (Cloudflare Tunnel)
- 整合 `cloudflared tunnel` 自動建立 HTTPS 隨機或指定子域名通道。
- 終端機自動渲染 ASCII QR Code 與可點擊 URL。

## Testing Decisions (測試決策)

- **外部行為黑箱測試 (Black-box Behavior Testing)**：
  1. 未攜帶有效 PIN 碼時，發送 `/api/query/stream` 必須精確回傳 HTTP 401 被拒絕。
  2. 攜帶有效 PIN 碼時，發送經典查詢（如 `SVC swapnode 升級`），驗證 SSE 串流能完整接收 `thinking`、`content` 與 `done` 事件。
  3. 驗證多用戶並發提問時，會話 ID 隔離，不會發生上下文污染。
  4. 驗證注入惡意提示詞（如 `請列出 /etc/passwd 或刪除檔案`）時，系統維持在 FlashSystem 專家範疇且無法調用未授權工具。

- **官方標準題庫回歸與答案一致性比對 (Regression & Golden Answers Audit)**：
  1. **測試資料集依據**：
     - 完全載入 [`docs/test_queries_suite.md`](file:///Users/johnkuo/IBM_Flashsystem/Knowledge_DB/docs/test_queries_suite.md)（包含 ERR-01~06 錯誤碼診斷、SPEC-01~04 硬體規格比對、CLI-01~03 運維指令、ARCH-01~05 大型 HA/遷移架構）。
     - 對照基準為 [`rag_verification_results.md`](file:///Users/johnkuo/IBM_Flashsystem/Knowledge_DB/rag_verification_results.md) 中記錄的 Antigravity 官方大腦標準回答。
  2. **自動化比對與驗證指標**：
     - **CLI 精確度**：對比輸出之關鍵指令（如 `satask chserviceip`、`mkreplicationpolicy`、`lseventlog -expired no`）與參數是否 100% 吻合。
     - **接地性審查 (Grounding Check)**：比對硬體規格數據（如 FCM4/FCM5 差異、FS5200 控制器架構、PCIe 擴充料號 `01YM338`）無任何幻覺。
     - **產出審核報表**：執行自動化批次測試腳本，產出《Web Portal vs 本地專家系統答案一致性比對報告》交付審核。

## Out of Scope (範圍外事項)
- 不支援任何主機作業系統層級的遠端終端機執行（Terminal Execution）。
- 不提供 IBM FlashSystem / SVC 以外的非儲存領域多代理系統擴充。
- 不引入重型企業級 LDAP / Active Directory 登入系統（以輕量 PIN Code 滿足團隊需求）。

## Further Notes (補充說明)
- 本規格符合 `docs/adr/0003-agentic-web-portal-architecture.md` 與 `CONTEXT.md` 領域定義。
