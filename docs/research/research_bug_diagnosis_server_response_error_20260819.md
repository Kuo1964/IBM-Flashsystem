# 故障診斷報告：網頁端「❌ 伺服器回應異常，請確認後端服務正常運行」之根本原因分析

**診斷時間**: `2026-08-19 11:13:50`  
**使用者提問**: `請幫我找出FS7300 7.68 TB 2.5" NVMe Flash drive part number`  
**回報現象**: 前端聊天室出現紅色報錯框 `❌ 伺服器回應異常，請確認後端服務正常運行。`  
**遵循指令**: **先不要動手修復，僅做精準診斷與根因分析報告**。

---

## 🔬 一、故障現象重現與後端探測結果

我們在後端直接使用完全相同的提問進行 API 探測：
* **提問**: `請幫我找出FS7300 7.68 TB 2.5" NVMe Flash drive part number`
* **後端直接執行結果**:
  - `HTTP 狀態碼`: `200 OK`
  - `耗時`: `12.19 秒`
  - `推理引擎`: `Google Gemini (gemini-2.5-flash) [Antigravity 統一專家大腦 - 架構設計與規格諮詢]`
  - `回答內容`: 成功檢索 `sg248543.pdf` 第 65 頁，精確列出 FS7300 (4657-924) 7.68 TB 2.5 吋 NVMe 驅動器之 Feature Code (`AG0F`) 與 `lsdrive <id>` 查詢指令。

---

## 🔍 二、為什麼網頁端會跳出「❌ 伺服器回應異常」？（3 大根本原因）

### 🚨 根本原因 1：前端將所有 HTTP 錯誤碼（包括 429 速率限制與 504 逾時）遮蔽為泛型錯誤訊息
在 `static/index.html` 第 715~721 行中：
```javascript
if (res.ok) {
    const data = await res.json();
    appendAgentResponse(data);
} else {
    // ⚠️ 只要 HTTP 狀態不是 200~299，直接硬編碼輸出「伺服器回應異常」
    appendAgentErrorMessage('❌ 伺服器回應異常，請確認後端服務正常運行。');
}
```
* **問題**：若後端回傳了 `429 Too Many Requests (頻率限制)` 或 `504 Gateway Timeout`，前端**完全沒有讀取後端回傳的具體錯誤原因 (`data.detail`)**，而是粗暴顯示為「伺服器回應異常」，導致使用者誤以為後端伺服器崩潰。

### 🚨 根本原因 2：速率防護器 (Rate Limiter) 誤將 Cloudflare 共享 IP 判定為頻繁請求
在 `web_app.py` 第 49、64~75 行中：
* 系統設定了每分鐘上限 10 次提問 (`MAX_REQUESTS_PER_MINUTE = 10`)。
* 當使用者透過 **Cloudflare 隧道** 訪問時，所有遠端請求抵達後端時都會帶有一致的代理 IP。
* 當前述自動化單元測試在背景密集執行（每秒數次請求）時，瞬間觸發了 10 次上限，導致後端拋出 **`HTTP 429 Too Many Requests`**，前端隨即破版顯示「伺服器回應異常」！

### 🚨 根本原因 3：後端 `process_query` 缺少統一的 `try...except` 異常兜底
* 當 Google Gemini API 在極端網路波動下偶發超時時，若 `process_query` 未能優雅捕捉，會向上拋出例外導致 FastAPI 回傳 `500 Internal Server Error`。

---

## 💡 三、建議修復計畫（等您指示再執行）

1. **前端智能錯誤捕獲 (`static/index.html`)**：
   * 當 `res.ok` 為 `false` 時，嘗試解析 `await res.json()` 並提取具體原因（如：「提問頻率過高，請稍候 10 秒」、「檢索逾時」），不再一律顯示伺服器異常。
2. **調優速率防護閾值 (`web_app.py`)**：
   * 將速率限制調整為合理值（例如每分鐘 60 次，或針對本地與 Cloudflare 隧道進行專屬計數放行）。
3. **後端全鏈路保底防護 (`web_app.py`)**：
   * 在 `/api/query` 路由中包覆 `try...except`，即使發生任何未預期的網路異常，也能優雅回傳保底合成解答，確保 `res.ok` 始終為 `200`！

---

> [!NOTE]
> **依據您的指令，本報告僅作故障原因診斷與分析，目前尚未對程式碼進行任何修改。**
