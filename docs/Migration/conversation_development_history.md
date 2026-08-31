# 🚀 IBM FlashSystem 知識庫 - 新機部署與轉移指南

本文件說明如何將整套 RAG 知識庫系統（包含程式碼、爬蟲架構與 5GB+ 的向量資料庫）無縫轉移到一台全新的 Mac 上，並恢復所有運作。

---

## 📦 階段一：核心資料庫轉移 (Data Migration)

因為真正的海量資料庫為求最高效能，並未放在 Google Drive 內，所以換新電腦時，您必須手動搬移這個隱藏資料夾。

1. **在「舊」電腦上**：
   將家目錄下的 `~/.ibm_flashsystem_kb` 整個資料夾複製到隨身碟或外接硬碟中。（因為檔案容量約 5GB，建議使用實體硬碟或透過區域網路傳輸，不建議直接上傳一般雲端空間）。

2. **在「新」電腦上**：
   將該資料夾原封不動地貼上到新電腦的「家目錄 (`~`)」底下。
   * **檢查方式**：打開終端機，輸入 `ls -lh ~/.ibm_flashsystem_kb/vector_db/chroma.sqlite3`，若能看到該檔案且大小為 4GB 以上，即代表資料庫轉移成功！

---

## 💻 階段二：取得程式碼 (Codebase Setup)

因為您的程式碼原本就建立在 Google Drive 中，轉移過程非常輕鬆：

1. 在新電腦上安裝並登入 **Google 雲端硬碟桌面版**。
2. 讓系統完成同步，您就能在新電腦的相同路徑下看到專案：
   `/Users/<您的新帳號>/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB`
3. 打開終端機 (Terminal)，使用 `cd` 指令進入該目錄。

---

## 🤖 階段三：地端 AI 模型佈署 (Ollama)

本專案強烈依賴地端的 Ollama 來執行向量化 (Embedding) 與推論。在我們的 `config.py` 中，指定了以下模型：
* **向量模型 (Embedding)**：`nomic-embed-text`
* **語言模型 (LLM)**：`llama3.2:latest`
* **視覺解析模型 (Vision)**：`llama3.2-vision`

您有兩種方式可以讓新電腦取得這些模型：

**方案 A：全新下載（推薦，最乾淨）**
1. 進入 [Ollama 官網 (ollama.com)](https://ollama.com/) 下載並安裝 Mac 版 Ollama。
2. 開啟終端機，依序輸入以下指令將模型抓下來：
   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3.2:latest
   ollama pull llama3.2-vision
   ```

**方案 B：離線完整複製（適合網速慢時使用）**
Ollama 的模型權重其實都存放在您的家目錄下。您只需要把舊電腦的 `~/.ollama` 整個隱藏資料夾，直接複製到新電腦的家目錄 `~` 下，新電腦安裝好 Ollama 後就能「瞬間」讀取到所有模型，不需重新下載！

---

## 🛠️ 階段四：建置 Python 執行環境 (Environment Setup)

由於 Python 的虛擬環境 (`.venv`) 包含了舊電腦的絕對路徑，**不能直接沿用**。我們必須在新電腦上重新建立：

1. **刪除舊的虛擬環境**（如果有被 Google Drive 同步過來）：
   ```bash
   rm -rf .venv
   ```
2. **建立全新的虛擬環境**：
   ```bash
   python3 -m venv .venv
   ```
3. **啟動虛擬環境**：
   ```bash
   source .venv/bin/activate
   ```
4. **安裝所有必備套件**：
   ```bash
   pip install -r requirements.txt
   ```

---

## 🌐 階段五：瀏覽器與 WAF 穿透準備

為了讓我們的爬蟲能繼續繞過 IBM Akamai WAF 的阻擋，新電腦必須具備以下條件：

1. **安裝正版 Google Chrome**：
   請確認新電腦上已經安裝了日常使用的 Google Chrome 瀏覽器（因為我們的程式碼 `channel="chrome"` 會呼叫系統原生瀏覽器來躲避偵測）。
2. **安裝 Playwright 驅動程式**（只需執行一次）：
   在啟動了虛擬環境的終端機內輸入：
   ```bash
   playwright install
   ```

---

## 🎉 階段六：最終驗證 (Verification)

完成上述所有步驟後，您的系統就完全復活了！您可以執行以下指令來確認一切正常：

**1. 測試資料庫搜尋 (RAG 驗證)**
透過您的 Antigravity 介面或終端機，發動 `@search_flashsystem_db`，若能瞬間給出正確解答，代表 5GB 資料庫連結成功。

**2. 測試爬蟲接續**
輸入指令測試爬蟲：
```bash
./.venv/bin/python ingest.py --url-only --workers 2 --max-pages 5
```
如果看到 `[跳過] 已在快取中` 或順利抓取新頁面，代表 WAF 穿透與爬蟲系統運作完美。
