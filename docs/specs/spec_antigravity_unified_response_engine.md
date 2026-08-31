# Feature Spec: Antigravity 統一專家大腦生成引擎 (Antigravity Unified Response Engine)

**標籤**: `ready-for-agent`  
**建立時間**: `2026-08-19 10:06:05`  
**相關分支**: `feature/enterprise-customer-service-portal`

---

## 1. Problem Statement (問題陳述)
目前 Web Portal 網頁端採用粗暴的分章節多 Prompt 拆分管線（Tier 4），導致大型架構/雙站點問題（如 PBHA IP Quorum 設計）生成了 3 個獨立子章節，引發：
1. **重複開場白與自我介紹**（「好的，客戶您好，我是...」在三個章節開頭各出現一次）。
2. **跨章節內容重複贅述**（三個章節都在重複講 Port 1260、80ms 延遲與 Java 啟動）。
3. **與 Antigravity IDE 專家模式輸出風格不一致**（IDE 輸出精煉、層次分明、無套話；Web 端輸出鬆散膨脹）。

---

## 2. Solution (解決方案)
將 Web 端推理架構全面升級為 **「Antigravity 統一專家大腦生成引擎 (Antigravity Unified Master Engine)」**：
1. **統一提示詞模組 (`prompts.py`)**：導入 Antigravity 頂級架構師統一提示詞範本，嚴格禁止重複客套與寒暄，強制使用結構化 Emoji（🏛️ 部署、🌐 網路、🛠️ 安裝、💻 代碼、⚠️ 注意事項）。
2. **單次全局融會貫通 (`rag_core.py`)**：廢除粗暴的三章節拆分，全面改為單次高質感生成（Single-Pass），結合 `thinkingBudget: 1024` 與 `Auto-Continue` 保險機制，實現**高達 7,000+ Tokens 正文容量、100% 零截斷、零重複贅述**。

---

## 3. User Stories (使用者故事)
1. **身為儲存工程師**，我在 Web 服務台詢問架構問題時，希望獲得像 Antigravity 一樣結構嚴謹、直擊核心的解答，以便我能立即掌握部署要點。
2. **身為客戶維運人員**，我希望解答中沒有重複三次的自我介紹與客套話，以便於閱讀時節省時間。
3. **身為系統架構師**，我希望雙站點 PBHA 與 IP Quorum 的解答中，網路延遲、頻寬、埠號只在專屬章節清晰列出一次，以便於資訊檢索與核對。
4. **身為 CLI 操作人員**，我詢問運維指令時，希望置頂標準 bash 程式碼區塊並附帶安全警告，以便於直接複製執行。
5. **身為系統管理者**，我希望所有回答的技術參數皆附帶 IBM 官方紅皮書頁碼標籤，以便於隨時追溯原廠出處。

---

## 4. Implementation Decisions (實施決策)
* **單一外部 Seam 設計 (Single Seam Discipline)**：
  - 外部調用介面保持不變：`rag_core.process_query(query_text: str, top_k: int = 25, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]`。
  - Web 端與 API 呼叫端無需任何修改，深度隱藏於 Module 內部。
* **統一提示詞範本 (`prompts.py`)**：
  - 新增 `build_antigravity_master_prompt(query_text: str, context_str: str, intent: str) -> str`。
  - 依據 `intent` 自適應調整輸出結構引導（架構 ➔ 🏛️ 部署 + 🌐 網路 + 🛠️ 安裝；指令 ➔ 💻 代碼置頂 + 參數表 + ⚠️ 安全警告）。
* **推理管線簡化 (`rag_core.py`)**：
  - `process_query` 統一調用 `build_antigravity_master_prompt` 進行單次深度生成，移除冗餘的三章節拆分循環。

---

## 5. Testing Decisions (測試決策)
* **Seam 測試原則**：在 `rag_core.process_query` 公共介面層進行端到端黑盒測試，不測試私有中間狀態。
* **驗證指標**：
  1. **零重複開場白**：回答中「好的，客戶您好」或自我介紹出現次數不超過 1 次。
  2. **經典 Emoji 結構**：架構題必須包含 `🏛️`、`🌐`、`🛠️` 三大分區。
  3. **頁碼引述完整**：包含 `[來源: 文檔.pdf, 第 X 頁]`。
  4. **零截斷保證**：輸出長度介於 1,000 ~ 2,500 字元，結尾標點符號完整。

---

## 6. Out of Scope (範圍外事項)
* 修改前端 HTML/CSS 介面（前端已支援 Markdown 與代碼複製，無需變動）。
* 重新處理向量資料庫索引（現有 57,538 筆切片無需更動）。
