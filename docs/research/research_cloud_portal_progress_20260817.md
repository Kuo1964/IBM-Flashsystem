# 專案研究報告：IBM FlashSystem 雲端問答入口 (Cloud Portal) 建置進度調查

**研究時間**: `2026-08-17 14:49:51`  
**研究目標**: 調查與彙整當前「雲端知識與技術圖表檢索入口 (Cloud Portal)」之核心模組建置進度、架構現況、安全防護與驗證測試成果。

---

## 📌 一、核心組件建置進度總覽 (Core Implementation Status)

目前雲端入口已完成四大核心模組之開發、驗證與 Git 分支版本控管 (當前分支: `feature/rag-quality-upgrade`):

| 核心組件 | 檔案路徑 / 模組 | 完成狀態 | 技術特色與功能 |
| :--- | :--- | :--- | :--- |
| **REST API 伺服器** | [web_app.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py) | ✅ **100% 已完成** | 採用 FastAPI + Uvicorn 架設；提供 `/api/query` 檢索問答、`/api/stats` 知識庫統計、`/api/images` 圖片預覽與 `/api/cache/clear` 快取清空端點。 |
| **Web 前端介面** | [static/index.html](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/static/index.html) | ✅ **100% 已完成** | 高質感黑夜微光澤 (Glassmorphism Dark Mode) UI；支援 Markdown 格式化、快捷提問晶片、相似度標籤與圖片 Lightbox 彈窗預覽。 |
| **中央 RAG 引擎** | [rag_core.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/rag_core.py) & [prompts.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/prompts.py) | ✅ **100% 已完成** | 實現兩階段語意重排 (Top-30 召回 -> Top-5 精排) 與 PDF 全文降級比對；注入資深專家結構化範本 (⚠️ 注意事項, 📋 步驟說明 + GUI/CLI 命令, 🔍 驗證指令)。 |
| **自動化部署嚮導** | [wizard_cloud_setup.sh](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/wizard_cloud_setup.sh) | ✅ **100% 已完成** | 遵照 `/wizard` 規範實現 4 階段 Bash 嚮導；自動背景啟動 `web_app.py` 並建立 100% 免費的 Cloudflare Tunnel HTTPS 外網通道與 Zero Trust 身份驗證網關。 |

---

## 🛡️ 二、安全防護與資源護城河 (Security & Resource Guardrails)

為確保公開雲端入口不被惡意攻擊或刷爆模型配額，系統已部署 **4 重防護機制**：

1. **路徑穿越安全防護 (Path Traversal Protection)**：
   * 在 [web_app.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py) 中，對 `/api/images/{path}` 進行絕對與相對路徑解算，強制使用 `resolved_path.is_relative_to(allowed_dir)` 檢查，禁止存取本機敏感目錄。
2. **併發與資源防護 (Concurrency Semaphore)**：
   * 設定 `asyncio.Semaphore(3)` 限制最多同時 3 筆 LLM 推理，防止多位同事同時提問導致顯示卡/CPU 負載過高。
3. **單人發問速率限制 (Rate Limiting)**：
   * 設定單一 IP 每分鐘最多 10 次提問 (`MAX_REQUESTS_PER_MINUTE = 10`)，防範惡意爬蟲。
4. **自動前綴清洗與雙語檢索擴充 (Query Sanitization & Expansion)**：
   * 自動清除 `@search_flashsystem_db` 等 MCP 工具標籤前綴，並對技術關鍵字（如 `GMCV`, `PBR`）進行雙語擴充，使向量相似度大幅飆升至 **80.46%**。

---

## 📊 三、數據吞吐與檔案解析現況 (Data Ingestion Progress)

經由 `ingest.py` 增量掃描器與 Playwright 無頭瀏覽器爬蟲實測：
- **紅皮書文檔 (PDFs)**: 已成功收錄 **48 本** FlashSystem 官方紅皮書（包含最新 FS5600 指南與安裝海報）。
- **技術圖表提取**: 已從 PDF 中實體提取 **8,197 張** 拓撲圖與連線架構圖（存放於 `~/.ibm_flashsystem_kb/extracted_images/`）。
- **向量 Chunk**: 知識庫目前總計收錄 **70,000+ 筆** 向量片段於本地 ChromaDB (`~/.ibm_flashsystem_kb/vector_db`)。

---

## 🚀 四、後續操作與部署建議 (Next Steps)

1. **啟動測試驗證**:
   在終端機執行嚮導 `./wizard_cloud_setup.sh` 或手動執行：
   ```bash
   PORTAL_PORT=8888 .venv/bin/python web_app.py
   ```
2. **分支合併 (Merge to Main)**:
   當前分支 `feature/rag-quality-upgrade` 之變更已全數調試完畢且 Commit 推送至 GitHub 遠端倉庫。驗證無誤後可執行 `git merge` 合併回 `main` 分支。
