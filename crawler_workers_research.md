# Playwright 網頁爬蟲並發數 (Workers) 擴充技術評估報告

## 1. 硬體能力分析 (Apple M5, 10 Cores, 24GB RAM)
在評估使用 `ProcessPoolExecutor` 搭配 Headless Chromium 的承載力時，需同時考量 CPU 與記憶體消耗：
*   **記憶體 (RAM) 承載力：** 24 GB 的記憶體相當充裕。單一個 Headless Chromium 實例在執行網頁渲染與 DOM 解析時，約消耗 200MB 至 500MB 記憶體（視頁面複雜度而定）。
    *   目前 6 個 workers 約消耗 1.2GB - 3GB。
    *   即使擴充至 20 個 workers，記憶體消耗約為 4GB - 10GB，仍遠低於系統上限。**記憶體並不會是系統的瓶頸**。
*   **處理器 (CPU) 承載力：** Apple M5 具備 10 核心。Chromium 本身即為多進程架構（包含 Browser, Renderer, Network 等），在密集解析動態網頁時對 CPU 的消耗極大。
    *   為了避免過度頻繁的 Context Switch（上下文切換）造成額外開銷，Worker 數量不應超過物理核心數。扣除作業系統背景服務與 Python 主進程（負責分配任務與資料庫寫入）的消耗，**8 到 10 個 workers 是 CPU 運算效率的理論極限**。若強行開啟超過 10 個 workers，單一網頁的解析時間將被拉長，總體吞吐量（Throughput）反而會下降。

## 2. 潛在瓶頸 (Bottlenecks)
除了本機硬體限制，系統架構與外部網路環境才是真正的考驗：
*   **SQLite/ChromaDB 並發寫入鎖定 (Database is locked)：**
    *   `ProcessPoolExecutor` 建立的是完全獨立的進程（Processes）。若多個進程同時嘗試對同一個 SQLite 檔案或本地 ChromaDB 進行寫入，極易觸發 `sqlite3.OperationalError: database is locked`。
    *   隨著 worker 數量增加，寫入衝突的機率呈指數上升。
*   **網路頻寬與 Socket 耗盡風險：**
    *   大量並發請求會同時佔用多個本機連接埠 (ephemeral ports)。若爬蟲未妥善關閉連線，產生大量 TIME_WAIT 狀態，可能會導致 Socket 耗盡。此外，高並發也會導致網路 I/O 擁擠，造成 Playwright 頻繁出現等待超時 (TimeoutError)。
*   **IBM 伺服器端的防爬蟲機制 (WAF, 429 Too Many Requests)：**
    *   IBM Docs 等企業級服務前方必定部署有 Web Application Firewall (如 Akamai 或 Cloudflare) 與 API 頻率限制 (Rate Limiting)。
    *   來自單一 IP 的高頻發請求（如每秒超過數十次）極易觸發 HTTP 429 錯誤、要求填寫驗證碼，甚至直接切斷 SSL 連線 (SSL Handshake Failure)。**這是提升 worker 數量時最先遇到且最致命的外部瓶頸**。

## 3. 結論與建議
**問題一：增加 workers 是否會更快？**
*   **不一定。** 單純從硬體角度來看，從 6 提升到 8 或 10 會有小幅度的效能提升。但在實際執行時，由於 IBM 伺服器的 429 限制與本地端資料庫的多進程寫入鎖定，盲目增加 worker 數量反而會導致大量的重試 (Retries)、連線超時與資料庫報錯，整體爬取速度甚至會因為不斷觸發防禦機制而變慢。

**問題二：建議的最大 workers 數量設定為多少？**
*   **最佳平衡點建議設定：6 到 8 個 workers。**
*   **硬體極限設定：10 個 workers。** (強烈建議不要超過 10，因為 M5 僅有 10 核心)

**後續架構優化建議 (若要進一步提升爬蟲穩定性與速度)：**
1.  **實作生產者-消費者模式 (Producer-Consumer)：** 將爬取任務 (Playwright) 與寫入任務 (ChromaDB/SQLite) 分離。使用 `multiprocessing.Queue` 讓多個爬蟲 worker 僅負責抓取與解析，將資料送回主進程 (或單一專職寫入的進程) 統一寫入，徹底解決 Database is locked 問題。
2.  **加入智慧退避機制 (Exponential Backoff)：** 若偵測到 HTTP 429 或 SSL 斷線，應立即暫停該 worker 數秒至數分鐘，避免 IP 遭到長時間封鎖。
3.  **啟用 SQLite WAL 模式：** 若仍需多進程操作資料庫，請確保 SQLite 開啟了 WAL (Write-Ahead Logging) 模式以提高並行讀寫能力。
