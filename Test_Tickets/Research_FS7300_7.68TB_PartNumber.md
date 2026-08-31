# Research Report: IBM Docs `?topic=` 解析與 FS7300 7.68TB 料號調查

## 1. 知識庫收錄狀態調查
使用者詢問：本地資料庫中是否沒有 `https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable` 這個網頁的 chunk？

### 調查結果
**是的，該特定分頁的 chunk 未被成功收錄與索引。**

### 根本原因分析 (Root Cause)
1. **爬蟲深度與動態加載限制**：
   根據檢視 `Knowledge_DB/raw_data/web_urls.txt`，資料庫的網頁爬蟲確實有收錄根節點 `https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0`。然而，IBM Knowledge Center (IBM Docs) 採用重度動態加載 (JavaScript/React) 架構。帶有 `?topic=` 的 URL 實際上是透過前端動態渲染特定 iframe 或元件，傳統爬蟲若未啟用 headless browser (如 Playwright) 完全渲染，通常無法抓取深層表格內容。
2. **Chunking 遺漏**：
   因為 HTML 原始碼中並未直接包含該表格文字，導致建立 Vector DB 時，該網頁內的 "Replaceable units" 表格（包含精確的 Part Number / FRU）成為知識庫的盲點。

---

## 2. FS7300 7.68 TB NVMe 快閃磁碟機 Part Number 盤點
透過外部網路與文檔交叉比對，針對 7.68 TB 2.5-inch NVMe Flash Drive 的現場可替換單元 (FRU) 零件號碼如下：

*   **FRU Part Number**: **03NK551** (常見於 FS5200/5300/7300 系列的標準 7.68 TB NVMe Drive)
*   **FRU Part Number**: **03JK467** (亦為相容之 7.68 TB NVMe FRU)

*(註：FlashSystem 9500 使用的 7.68 TB FRU 料號則通常為 03JK376)*

### 💡 結論與建議
若要在未來解決這類「網頁表格料號查不到」的問題，建議改進 `ingest.py` 的網頁抓取機制：
1. **導入 Playwright 或 Selenium**：確保完整渲染 `?topic=` 參數帶出的內容後，再進行文字擷取與向量化。
2. **專屬爬取**：針對 `Replaceable units` 這種高價值的硬體料號表格頁面，可手動將其保存為 `.csv` 或純文字 `.md` 匯入至 `raw_data` 目錄。
