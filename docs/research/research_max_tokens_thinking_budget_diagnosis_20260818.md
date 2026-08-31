# 診斷報告：Gemini 2.5 Flash 內部思考 Token 擠佔導致單次問答截斷原因分析

**診斷時間**: `2026-08-18 13:44:20`  
**問題語句**: `請給我一個PBHA IP Quorum設定的建議如果我的兩個FS5600系統放在兩個不同的site IP Quorum該怎麼設計`  
**現象描述**: 回覆生成至 `| 項目 | 規格` 時突然被截斷，耗時 44.93s。

---

## 🔍 根本原因精確定位 (Root Cause)

1. **Gemini 2.5 Flash 思考 Token (Thoughts Tokens) 佔用限制**：
   * 實測 Log 顯示：
     * `Finish reason`: **`MAX_TOKENS`**
     * `candidatesTokenCount`: **8192** (已達到 API 單次生成的上限 8192)
     * `thoughtsTokenCount`: **5820 Tokens**（大模型內部深度思考推論消耗了 5820 個 Tokens！）
     * **實際留給正文輸出的剩餘空間僅剩**：`8192 - 5820 = 2372 Tokens`（約 1,000 多個中文字）。
   * 當大模型在深度思考後開始撰寫詳盡的 IP Quorum 架構正文與表格時，正文寫到第 2372 個 Token 就觸碰到了 8192 總上限，導致硬性截斷在表格標題 `| 項目 | 規格`！

2. **意圖分類流向問題 (Intent Misclassification)**：
   * 該提問屬於「雙站點跨站架構設計與建議 (Dual-site Architecture Design)」，但被判定為 `tier2_spec`（單次問答模式），未被分流至 `tier4_architecture`（多章節並行鏈式生成管線）。
   * 若進入 Tier 4 鏈式管線，三個章節各自擁有獨立的 8192 Tokens 空間，總容量達 24,576 Tokens，絕不會發生截斷。

---

## 💡 徹底解決方案 (供審查，先不執行)

1. **關閉/限制思考 Token 預算 (Thinking Budget Control)**：
   * 在 Gemini 2.5 API 的 `generationConfig` 中加入 `thinkingConfig: {"thinkingBudget": 1024}`（或在常規問答模式關閉過度的思考耗額），將 7,000+ Tokens 空間 100% 保留給正文輸出。
2. **意圖分類擴展 (Intent Keyword Expansion)**：
   * 將「`設計`」、「`建議`」、「`架構`」、「`雙站點`」、「`跨站點`」、「`site`」、「`規劃`」等大型架構諮詢納入 `tier4_architecture` 萬字鏈式生成，徹底避免任何單次生成超額問題。
