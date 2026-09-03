# 0003. Agentic Storage Web Portal 架構與安全穿透決策

Date: 2026-09-03

## 狀態 (Status)
Accepted

## 背景與問題 (Context)
用戶與團隊同仁需要在手機與電腦等多裝置上，透過網際網路提問 IBM FlashSystem / SVC 儲存架構問題。
傳統單次檢索的 Web API (Naive RAG) 缺乏 Agent 的多輪思考、工具審計 (Grounding Auditor) 與反覆驗證，容易產生幻覺。
同時，將專家系統開放給同事使用時，必須兼顧系統安全（防止 Prompt Injection 或惡意系統指令執行）、會話隔離與存取授權。

## 決策 (Decision)
1. **Agentic Storage Gateway 推理核心**：
   - 採用 ReAct 多輪 Agent 推理架構，使用 Gemini 3.7 Flash/Thinking 核心。
   - 整合本地 ChromaDB 向量檢索、PDF 架構圖多模態解析與 Grounding 比對驗證，保證輸出品質與 Antigravity IDE 專家會話 100% 一致。
   - 執行環境嚴格限定在「唯讀沙盒 (Read-Only Sandbox)」，嚴禁暴露本機終端機指令或檔案寫入工具。
2. **安全防護 (PIN Access Guard)**：
   - 入口設置全團隊共用的 PIN 碼驗證機制。
   - 限制每分鐘請求頻率 (Rate Limiting) 與請求併發隊列 (Semaphore)，保障本地資源與 API 配額。
3. **網際網路發布 (Cloudflare Mobile Portal)**：
   - 透過 Cloudflare Tunnel 建立外網 HTTPS 加密通道，無需更動路由器 NAT/防火牆或暴露固定 IP。
4. **現代化響應式 UI (Mobile & Desktop)**：
   - 支援手機/平板/電腦自適應 (Glassmorphic 風格)。
   - 支援 SSE 串流打字輸出、Markdown 語法解析、CLI 指令一鍵複製與 FlashSystem 架構圖彈窗檢視。

## 後果與影響 (Consequences)
- **正面效益**：同仁隨時隨地能獲取與本地 IDE 完全相同的精確診斷與 CLI 配置，且本機環境完全隔離安全。
- **維護考量**：需確保本機背景服務 (`web_app.py` + `cloudflared`) 持續運行以維持外網連線可用性。
