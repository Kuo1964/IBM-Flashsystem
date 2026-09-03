# 深度調研報告：為什麼同樣的問題在 Antigravity 視窗與 Web 端會有不同的處理鏈路與輸出？ (Divergence Research)

## 📌 研究背景
使用者提問：
> 「為什麼 1500 這個資源在這個 Antigravity 的系統不會被誤判？我很清楚的要求，同樣的問題在這個專家系統和網站輸入後續的處理程序應該一模一樣。到底哪裡不一樣？」

本報告針對 **「Antigravity 對話視窗環境」** 與 **「Web Portal 網站請求鏈路」** 的全流程進行深度溯源與機制對比，揭示兩者在推理機制、檢索路徑與 Context 組裝上的根本差異。

---

## 🔍 核心機制對比：兩條完全不同的處理程序

| 維度 | Antigravity 專家視窗 (當前對話) | Web Portal 網站端 (`web_app.py`) |
| :--- | :--- | :--- |
| **1. 處理主體** | **自主 Agentic 思考大腦 (LLM Agent)** | **機械式 Python RAG 腳本管道 (Pipeline)** |
| **2. 語意語境理解** | **深度理解全句語意**：<br>大腦知道「MTU: 1500 改成 9000」中的 `1500` 是乙太網路 Maximum Transmission Unit 數值，絕非儲存故障代碼。 | **盲目正則提取 (Regex Token Extraction)**：<br>`re.findall(r'(0\d{5}\|[1-9]\d{2,3})')` 機械式將 `1500` 提取為候選代碼。 |
| **3. 檢索與穿透機制** | 大腦依據全域知識與意圖，綜合判斷 FS5030 與 iSCSI Jumbo Frame 規範。 | 機械式觸發 `antigravity_code_search("1500")`，從 78 萬 Chunks 中硬拉出包含 `1500` 的 ATM 機型，給予 190.0 分最高權重塞滿 Context。 |
| **4. 系統提示詞約束** | 具備靈活的推理與儲存架構先驗知識，注重給出可落地的完整解決方案。 | 受到嚴格的防幻覺約束：<br>*「嚴禁憑空推測，凡 Context 內無明確記載者一律回答原廠未記載」*。 |
| **5. 最終產出結果** | 產出包含架構、全鏈路一致性與 `chportethernet` 的標準解答。 | 因 Context 被 ATM 1500 雜訊塞滿，模型遵守防幻覺約束，老實輸出「*資料未記載 MTU 調整指令*」。 |

---

## 🚨 根本差距分析 (The Root Cause of Divergence)

1. **為什麼 1500 在 Antigravity 不會被誤判？**
   - 因為 Antigravity Agent 擁有完整的上下文注意力機制（Attention Mechanism），能自動識別 `MTU: 1500` 的語境是「網路封包大小」，因此絕不會把 1500 當作錯誤代碼去搜尋硬體故障記錄。
2. **為什麼 Web 端會被誤判？**
   - Web 端並非直接由 Antigravity Agent 互動式接管，而是由 [`web_app.py`](file:///Users/johnkuo/IBM_Flashsystem/Knowledge_DB/web_app.py) 呼叫 [`vector_store.py`](file:///Users/johnkuo/IBM_Flashsystem/Knowledge_DB/vector_store.py) 的檢索代碼。
   - 在 `vector_store.py` 中，我們先前為了抓取 `1059` / `2560` 等錯誤碼，寫了一段「**只要看到 4 位數字就無條件執行代碼穿透**」的靜態正則。
   - 這段正則缺乏了語意過濾，把網路數值 `1500` 誤當成錯誤碼，硬塞給了後端的 Gemini API，造成 Context 污染。

---

## 🎯 如何徹底實現「Web 端與 Antigravity 處理程序完全一模一樣」？

要達成您所要求的「雙端處理程序 100% 一致」，必須在 Web 後端的 RAG 管道中融入與 Antigravity 相同的語境智慧：
1. **語意前置過濾 (Semantic Filtering)**：
   在提取代碼前，先進行語境判定（只有在包含「error/錯誤/代碼/event/故障」時才啟動代碼穿透；對於包含「MTU/Port/速度/數值」等數值，嚴禁觸發代碼穿透）。
2. **檢索注入對齊**：
   確保 Web 端 RAG 注入 Context 的內容與 Antigravity 大腦調用的知識完全同源、乾淨無雜訊。
