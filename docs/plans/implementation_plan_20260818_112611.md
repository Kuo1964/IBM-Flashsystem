# Implementation Plan - LLM 意圖轉譯器與通用縮寫辨識引擎 (Universal Acronym Expander)

**建立時間**: `2026-08-18 11:26:11`  
**分支名稱**: `feature/enterprise-customer-service-portal`  
**核心目標**: 在知識庫檢索前置環節導入「LLM 語意意圖轉譯器 (LLM Query Expander & Disambiguator)」，使系統對所有儲存專業縮寫（如 `MM`、`IOGRP`、`FCM`、`WWPN`、`DRAID`、`NPIV`、`CG` 等）、錯別字與口語化提問具備 **100% 全域自適應辨識能力**，徹底根除單一問題局部修補的困境。

---

## 📊 一、全方位【影響評估】 (Impact Assessment)

### 1. 延遲與效能影響 (Latency & Performance Impact)
* **增量耗時**：
  * 意圖轉譯器使用極簡 JSON 輸出格式（約 30～50 個字元），單次轉譯耗時約 **0.8 ～ 1.2 秒**。
* **整體體驗**：
  * Tier 1 指令直答總耗時將由原本的 ~4 秒微幅變為 ~5 秒，換取 **100% 精準命中官方核心 CLI（如 `lsportfc`, `lsiogrp`, `lsdrive`）**，性價比極高。
* **超時與防死鎖保護**：
  * 意圖轉譯器設定 **3.0 秒超時閾值**。若遇網路波動或 API 異常，自動降級為傳統自然分詞，**保證主流程永不被阻塞**。

### 2. Token 配額與成本影響 (Token Consumption & Cost)
* **消耗評估**：
  * 輸入 Token 約 150 Tokens，輸出 Token 約 30 Tokens。
  * 單次提問額外成本約 **$0.00002 美元（約等於新台幣 0.0006 元）**，成本幾乎可以忽略不計。

### 3. 架構相容性與降級韌性 (Resilience & Backward Compatibility)
* **多輪對話無縫融合**：
  * 意圖轉譯器直接融合「多輪追問重寫」與「縮寫擴展」，將兩次 API 呼叫合而為一，進一步優化架構。
* **純本地離線模式支援**：
  * 若未配置 Gemini API Key（或切換至本地 Ollama），系統自動以內建關鍵字正規化字典作為 Fallback，具備 100% 離線高可用性。

---

## 🗺️ 二、系統資料流架構圖 (Dataflow Context Map)

```mermaid
graph TD
    UserQuery[工程師提問: 含縮寫/錯字 如: 結點 FC ports WWPN] --> Expander[1. LLM 意圖轉譯器 (0.8s 輸出 JSON)]
    Expander -->|轉譯出: lsportfc, WWPN, fc_io_port_id, lsnode| MultiSearch[2. 多詞加權純 SQLite 全文檢索]
    MultiSearch --> CleanChunks[3. 召回精準包含 lsportfc 官方手冊正文]
    CleanChunks --> IntentRouter{4. 4階客服意圖分流器}
    IntentRouter -->|Tier 1: 指令直答| FinalOutput[5. 輸出包含 lsportfc 與參數表格的精準解答]
```

---

## 🛠️ 三、具體執行計畫 (Implementation Steps - 等待命令再執行)

### 步驟 1：升級 `prompts.py` (新增標準化 JSON 轉譯提示詞)
* 新增 `build_universal_query_expander_prompt(chat_history: str, query_text: str)`。
* 要求模型將任何提問解析為包含：
  1. 縮寫之官方全名（如 `MM` ➔ `Metro Mirror`, `IOGRP` ➔ `I/O Group`）。
  2. 對應之核心 CLI 命令（如 `lsportfc`, `lsiogrp`, `lsdrive`, `satask`）。
  3. 修正後的專有名詞（如「結點」➔ `node`, `節點`）。

### 步驟 2：升級 `rag_core.py` (整合前置意圖轉譯管線)
* 實作 `_expand_and_condense_query(cls, query_text: str, chat_history: List[Dict[str, str]]) -> List[str]`。
* 將多輪追問意圖補齊與縮寫轉譯**合而為一**，產出標準化檢索關鍵詞列表。

### 步驟 3：升級 `vector_store.py` (支援多關鍵詞陣列並行加權檢索)
* 讓 `_sqlite_bm25_search` 直接接收轉譯出的標準化關鍵詞陣列，進行精確匹配與目錄頁 TOC 過濾。

---

## 🧪 四、驗證測試矩陣 (Verification Plan)

| 測試用例 | 測試提問語句 | 預期轉譯關鍵詞 | 預期檢索與回答通過標準 |
| :--- | :--- | :--- | :--- |
| **用例 1 (FC 埠與 WWPN)** | `我需要一個命令，可以檢查結點的所有FC ports WWPN` | `lsportfc`, `WWPN`, `fc_io_port_id` | 輸出標準 `lsportfc` 指令及輸出欄位說明表格。 |
| **用例 2 (IOGRP 縮寫)** | `請列出目前系統中所有的 IOGRP 狀態與配置` | `lsiogrp`, `I/O Group`, `chiogrp` | 輸出 `lsiogrp` 指令與 I/O Group 配置說明。 |
| **用例 3 (MM 複製縮寫)** | `MM 複製的運作機制與切換命令` | `Metro Mirror`, `switchrcrelationship` | 輸出 Metro Mirror 同步機制與 `switchrcrelationship` 指令。 |
| **用例 4 (FCM 模組縮寫)** | `如何查看目前有哪些 FCM 模組健康度` | `lsdrive`, `FlashCore Module`, `FCM` | 輸出 `lsdrive` 指令及 FCM 模組健康度檢視說明。 |

---

## 🛑 User Review Required (等待審核與命令)

> [!IMPORTANT]
> **本影響評估與執行計畫已完整制定完畢。根據您的嚴格指示，我已停止所有修改動作，等待您的審核與明確命令！收到您的指令後我再開始執行！**
