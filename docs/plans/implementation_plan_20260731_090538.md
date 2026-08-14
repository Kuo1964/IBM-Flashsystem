# IBM FlashSystem 專家系統與 RAG 知識庫建構計畫

**時間戳記**: `2026-07-31 09:05:38`

本計畫旨在構建一個完全本地化（Local & Private）的 IBM FlashSystem 專家系統知識庫。利用 Ollama (LLM/Embedding/Vision)、ChromaDB 向量資料庫、多模態 PDF 圖片摘要解析技術，以及 MCP (Model Context Protocol) 伺服器架構，實現跨 AI Agent（如 Antigravity, Claude Desktop, AnythingLLM）調用的高精準度檢索系統。

---

## 🎯 架構目標與特點

1. **完全本地運行 (Local & Private)**：透過 Ollama 提供嵌入模型 (Embedding Model)、LLM 與 Vision 多模態模型，數據完全保留於本機。
2. **多模態 PDF 圖表解析 (Vision Multimodal RAG)**：
   - 提取 PDF 紅皮書內文與原始圖表（如 SAN 連線架構圖、RAID 配置圖、效能分析圖）。
   - 呼叫 Ollama 視覺模型生成圖表的專業技術摘要並儲存於向量庫。
   - 查詢時除了返回文字解答，亦能引述圖片檔名與原 PDF 頁碼。
3. **增量更新機制 (Incremental Ingestion Pipeline)**：
   - 建立 `manifest.json` 追蹤文件 Hash 與修改時間。
   - 未來新增/更新網址或紅皮書時，僅對新變動進行解析與向量化。
4. **標準 MCP Server 介面**：
   - 建立 `mcp_server.py`，使 Antigravity、Claude Desktop 或其他 Agent 能夠透過標準工具調用（Tool Calls）查詢知識庫。
5. **相容性與備份**：
   - 原始文件存於 Google Drive 目錄 (`raw_data/`)。
   - 向量庫與圖檔索引隔離儲存，避免雲端同步鎖定。

---

## 📂 專案目錄結構

```text
/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/
├── raw_data/                 # 原始資料夾 (雲端硬碟同步)
│   ├── pdfs/                 # 放置 IBM FlashSystem 紅皮書 PDF 檔案
│   └── web_urls.txt          # 放置 IBM 官方網站與文檔連結
├── extracted_images/         # 從 PDF 提取出的圖表圖片 (按 PDF 檔名分類)
├── vector_db/                # 本地 ChromaDB 向量資料庫儲存區
├── manifest.json             # 檔案 Hash 記錄檔 (用於增量更新)
├── config.py                 # 專案配置檔 (Ollama URL, 模型名稱, 路徑)
├── parser.py                 # PDF 內文與圖表提取器 (PyMuPDF)
├── vision_processor.py       # Ollama 視覺模型圖表摘要生成器
├── vector_store.py           # ChromaDB 管理與 Ollama Embedding 切片儲存
├── ingest.py                 # 增量更新管道執行主腳本
├── mcp_server.py             # MCP (Model Context Protocol) 伺服器主程式
├── cli.py                    # 本地檢索測試與維護 CLI 工具
└── requirements.txt          # Python 依賴包需求清單
```

---

## ⚠️ 思考與評估事項 (User Review Required)

> [!IMPORTANT]
> **Ollama 本地模型配置確認**：
> 1. **Embedding 模型**：建議使用 `nomic-embed-text` 或 `bge-m3`。請確認您的 Ollama 已下載對應的 Embedding 模型。
> 2. **Vision 多模態模型**：為了解析 PDF 中的技術圖表，建議 Ollama 中安裝 `llama3.2-vision` 或 `qwen2-vl`。
> 3. **LLM 模型**：用於生成與回答（例如 `llama3.1` 或 `qwen2.5`）。

> [!NOTE]
> **Google Drive 檔案同步注意事項**：
> 原始 PDF 與網頁清單存放在 Google Drive 同步資料夾中，而 `vector_db/` 與 `extracted_images/` 建議存於本地路徑或隔離資料夾，避免檔案鎖定衝突。

---

## 🛠️ 導入步驟與模組設計 (Proposed Changes)

### 階段 1：基礎環境與設定
* 建立 `requirements.txt` 與 `config.py` 系統設定檔。

### 階段 2：PDF 內文/圖表提取與視覺摘要模組
* 採用 `PyMuPDF` 逐頁解析 PDF，提取純文字區塊與頁碼。
* 呼叫 Ollama 視覺模型生成繁體中文圖表描述與關鍵字標籤。

### 階段 3：向量資料庫與增量更新管道
* 初始化 ChromaDB 本地持久化資料庫與 Ollama Embedding 接口。
* 讀取 `manifest.json` 實現增量吞吐與更新。

### 階段 4：MCP 伺服器與 Agent 對接介面
* 使用官方 MCP Python SDK 實現 `mcp_server.py` 工具服務。
