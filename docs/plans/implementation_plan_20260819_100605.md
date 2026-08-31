# Implementation Plan - Antigravity 統一專家大腦生成引擎 (Antigravity Unified Response Engine)

**建立時間**: `2026-08-19 10:06:05`  
**分支名稱**: `feature/enterprise-customer-service-portal`  
**依據規範**: [`docs/specs/spec_antigravity_unified_response_engine.md`](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/docs/specs/spec_antigravity_unified_response_engine.md)  
**核心目標**: 將 Web 端推理管線全面升級為與 Antigravity IDE 專家模式 100% 一致的「統一專家大腦生成引擎」，實現 **零重複開場白、經典 Emoji 三段式結構、密集技術要點、頁碼精準引述與 100% 零截斷**。

---

## 🗺️ 一、Codebase Recon & Context Map (模組與 Seam 設計)

### 1. 模組深度與 Seam (依據 `/codebase-design` 原則)
```
┌────────────────────────────────────────────────────────┐
│ Public Seam: rag_core.process_query(query, top_k, ...) │ ← Small Interface
├────────────────────────────────────────────────────────┤
│ [Deep Implementation]:                                 │
│  - LLM 縮寫轉譯與意圖消歧義 (Universal Expander)        │
│  - SQLite BM25 自然分詞檢索 (25 Chunks + TOC Filter)   │
│  - Antigravity Master 提示詞工程 (Structure Synthesis)  │
│  - Single-Pass API 呼叫 (thinkingBudget: 1024)         │
│  - Auto-Continue 斷點續寫與 Markdown Auto-Healer       │
└────────────────────────────────────────────────────────┘
```
* **Leverage for Callers**: `web_app.py` 與 CLI 只需呼叫單一 `process_query` 函式，內部所有複雜度（檢索、提示詞、防截斷、格式癒合）全部封裝隱藏。
* **Locality for Maintainers**: 所有生成風格與提示詞集中於 `prompts.py`，邏輯集中於 `rag_core.py`，修改一次全域生效。

---

## 🛡️ 二、Guardrail Spec (品質與安全防護規格)

1. **零重複開場白 Guardrail**：
   * 提示詞強制嚴禁自我介紹與多餘問候，全局僅允許一個直入主題的引言。
2. **三維度經典結構 Guardrail**：
   * 架構問題自適應展開為：`🏛️ 一、部署位置與架構設計` ➔ `🌐 二、網路通訊與效能要求` ➔ `🛠️ 三、生成、安裝與安全規範`。
3. **思考預算與正文配額 Guardrail**：
   * 鎖定 `thinkingBudget: 1024`，確保大模型有足夠的推論空間，同時預留 7,000+ Tokens 保證正文完整輸出。
4. **Markdown 標籤閉合 Guardrail**：
   * `_heal_markdown_tags` 保證所有代碼區塊與粗體標籤合法閉合。

---

## 🧪 三、TDD 測試計畫 (依據 `/tdd` 規範 - Red ➔ Green 循環)

### 1. 測試檔案：`tests/test_antigravity_unified_engine.py`
* **Test Case 1 (PBHA IP Quorum 雙站點架構題)**：
  - 驗證輸出包含 `🏛️`、`🌐`、`🛠️` 三大標題。
  - 驗證「好的，客戶您好」或開場自我介紹出現次數 $\le 1$。
  - 驗證包含 `[來源: sg248569.pdf` 等官方頁碼標籤。
  - 驗證字數介於 1,000 ~ 2,500 字元且結尾語句完整。
* **Test Case 2 (CLI 修改 Service IP 指令題)**：
  - 驗證輸出置頂 ```bash 代碼區塊包含 `satask chserviceip`。
  - 驗證包含核心參數說明與安全警告。

---

## 🔍 四、Brownfield Diff Review (變更清單事前審查)

### 檔案 1：`prompts.py`
* 移除分散的 Tier 1~4 提示詞，統一導入 `build_antigravity_master_prompt(query_text, context_str, intent)`。

### 檔案 2：`rag_core.py`
* 簡化 `process_query`，移除粗暴的三章節拆分循環，統一由 `build_antigravity_master_prompt` 進行單次深度生成。

---

## 🛑 User Review Required (等待審核與命令)

> [!IMPORTANT]
> **本實作計畫已依據 `/to-spec`、`/codebase-design`、`/tdd` 與 `/code-review` 規範完整制定完畢。**  
> **根據您的嚴格指示，我已停止所有修改動作，等待您的審核與明確執行命令！**
