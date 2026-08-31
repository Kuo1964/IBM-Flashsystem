# Antigravity 專家系統 vs. Web 雲端問答系統之推理差異分析研究報告

## 📌 摘要 (Executive Summary)

本研究旨在釐清：**為什麼同一個問題（如 `CMMVC1035E`），在「Antigravity 專家系統」中能給出 100% 正確的磁區保護 (Volume Protection) 解答，而在「Cloudflare Web 網站」卻會產生節點離線的幻覺？**

---

## 🔬 核心架構差異對比 (Architectural Divergence)

| 維度 | Antigravity 專家系統 (Agentic AI) | Cloudflare Web 網站 (Single-Shot RAG) |
| :--- | :--- | :--- |
| **執行機制** | **自主 Agentic 思考循環 (ReAct Loop + Tool Use)** | **單次檢索生成 (Single-Shot Prompting)** |
| **工具調用能力** | 具備完整工具箱 (`search_web`, `sqlite3`, `view_file`, `run_command`) | **零外部工具**，僅依賴檢索召回的固定 Context |
| **當資料庫缺乏內文時** | 1. 發現本地 DB 只有目錄連結<br>2. **主動發起 Web 官方搜尋** 補全一手定義<br>3. 經多方驗證後才輸出 | 1. 收到只有超連結的目錄 Chunks<br>2. 無法調用外部工具補充資料<br>3. **被迫在 Context 缺失下進行臆測 (Hallucination)** |
| **錯誤自癒能力** | **高 (具備多輪自我反思與驗證機制)** | **無 (一次性 Pipeline，錯了就直接輸出)** |

---

## 🧩 關鍵成因深度剖析

```mermaid
flowchart TD
    subgraph Antigravity_Expert [Antigravity 專家系統]
        Q1[問題: CMMVC1035E] --> R1[查詢本地資料庫]
        R1 -->|發現只有目錄連結| T1[自動觸發 Tool: search_web 查詢 IBM 官方一手定義]
        T1 -->|取得完整本文| A1[輸出 100% 正確的 Volume Protection 答案]
    end

    subgraph Cloudflare_Web [Cloudflare Web 客服網站]
        Q2[問題: CMMVC1035E] --> R2[查詢本地資料庫]
        R2 -->|召回 5 個目錄連結 Chunks| P2[直接將 5 個目錄 Chunks 塞入 Prompt]
        P2 -->|模型無工具可查，上下文無定義| H2[模型根據 CMMVC 前綴聯想常規硬體故障 (產生幻覺)]
    end
```

### 1. Agent 智能循環 vs. 靜態 Pipeline
* **Antigravity** 是一個擁有全功能工具鏈的資深架構師 Agent。當它在回答您的提問時，如果發現本地資料庫僅有 `- [CMMVC1035E](/docs/...)` 這種目錄頁時，它不會瞎猜，而是會立刻在背景調用 `search_web` 與 IBM 官方即時文件進行 Cross-Check（交叉比對），確保資訊絕對真實可靠後才呈現給您。
* **Web 客服網站** 是一個輕量化的 Web 伺服器，受限於 API 架構，它採用的是典型的「檢索 -> 拼裝 Prompt -> LLM 單次輸出」。它沒有工具可以「走出去」聯網驗證，因此當檢索到的內容不完整時，大語言模型就只能「看圖說故事」，引發幻覺。

---

## 🛠️ 如何讓 Web 網站達到與 Antigravity 100% 一致的正確率？

1. **資料層 (Data Ingestion)**：將 IBM Messages and Codes（所有 CMMVC / 010xxx 代碼）的「本文定義」完整收錄進本地 78 萬筆資料庫，不讓 Web 端拿到只有超連結的「空殼目錄」。
2. **防護層 (System Grounding)**：在 `prompts.py` 中加入嚴格的「否定約束」——若 Context 中未包含該錯誤碼的明確解釋，禁止自由聯想節點離線或硬體故障。
