import json
import os
import sys
import time

sys.path.append("/Users/johnkuo/IBM_Flashsystem/Knowledge_DB")
import config
from rag_core import RAGEngine

queries = [
    "我的客戶想從傳統的GMCV轉換成PBR要怎麼做要注意什麼？詳細的流程是怎麼樣",
    "請給我一個PBHA IP Quorum設定的建議如果我的兩個FS5600系統放在兩個不同的site IP Quorum該怎麼設計",
    "FS5200 SAS adapter是額外插卡嗎還是內建的？給我看一下 node canister 的圖",
    "客戶原本使用 FlashSystem 5200 HyperSwap 的架構，他現在在第三地新購了一個 FS5600，他想用 PBHA 的方式抄寫資料到新購的 FS5600。以上是我們 proposed 的做法，再幫我們分析一下有什麼要注意的以及條列出詳細的步驟。 ，或者有更好的辦法嗎？ 做法 : １．ＦＳ５２００　ＨＡ　(Hyperswap) 先拆開，不做HA 2. FS5200  2台升級 Firmware 9.1.0.6 3. FS5200 建立HA (PBHA) 架構 4. 新購FS5600 用內建的IP Replicator (PBR)  功能將 FS5200 Lun 資料抄寫到竹南 FS5600",
    "客戶的資料存放在SVC加FS7300上面他新採購一台FS9600你有建議轉換資料的方式嗎主機的作業系統是AS400？",
    "FS7300 執行命令得到了一個錯誤訊息CMMVC8000E該怎麼處理",
    "Quad-port 32 Gbps FC adapter",
    "FS7300 7.68 TB 2.5\" NVMe Flash drive part number",
    "我想用Commend line來修改，service IP該怎麼做命令請提供給我",
    "请帮我比较 FS5200 以及 FS5300 和 FS5600 的主要差异",
    "找出以下這個FS7300零件的料號: 240 GB M.2 SSD",
    "请提供我FS5600 recovery system的步骤以及官方链接"
]

def main():
    print("=" * 70)
    print("🚀 開始執行 IBM FlashSystem 專家系統端到端 (End-to-End) RAG 驗證測試")
    print(f"📌 模型核心: {config.LLM_PROVIDER.upper()} ({config.GEMINI_MODEL}) + ChromaDB (78萬筆 Chunks)")
    print("=" * 70)

    output_file = "/Users/johnkuo/IBM_Flashsystem/Knowledge_DB/rag_verification_results.md"
    
    # 檢查已完成的題目
    completed_indices = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            for i in range(1, len(queries) + 1):
                if f"## 📌 Q{i}:" in content:
                    completed_indices.add(i)

    mode = "a" if completed_indices else "w"
    
    with open(output_file, mode, encoding="utf-8") as f:
        if not completed_indices:
            f.write("# IBM FlashSystem 專家系統 RAG 檢索與問答驗證報告\n\n")
            f.write("> **測試環境說明**：\n")
            f.write(f"> - **知識庫規模**：782,177 Chunks (包含最新 IBM 官方 Web 頁面與原廠 Redbooks)\n")
            f.write(f"> - **推理模型**：{config.LLM_PROVIDER.upper()} ({config.GEMINI_MODEL})\n")
            f.write(f"> - **檢索流程**：使用者提問 ➔ LLM 意圖轉譯與英文擴展 (Acronym Expander) ➔ ChromaDB 向量與原廠手冊雙通道檢索 ➔ 專家級答案合成\n\n")
            f.write("---\n\n")
            f.flush()
        
        for i, q in enumerate(queries, 1):
            if i in completed_indices:
                print(f"⏩ [Q{i}] 已存在於報告中，跳過...")
                continue
                
            print(f"\n[{i}/12] 處理問題: {q[:35]}...")
            start_t = time.time()
            
            # 1. 取得 LLM 英文擴展詞
            expanded_terms = RAGEngine._expand_query_terms_with_llm(q)
            
            # 2. 執行完整端到端推理
            res = RAGEngine.process_query(query_text=q, top_k=15)
            elapsed = round(time.time() - start_t, 2)
            
            intent = res.get("intent", "N/A")
            provider = res.get("provider", "N/A")
            sources = res.get("sources", [])
            answer = res.get("answer", "")
            
            print(f"  ✓ 完成 (耗時 {elapsed}s, 意圖: {intent}, 引用來源數: {len(sources)})")
            
            # 3. 寫入 Markdown 並立即 flush
            f.write(f"## 📌 Q{i}: {q}\n\n")
            f.write(f"- **🧠 意圖分類**: `{intent}`\n")
            f.write(f"- **🌐 LLM 轉譯與英文擴展關鍵詞**: `{', '.join(expanded_terms) if expanded_terms else '無 (直接使用原詞)'}`\n")
            f.write(f"- **⏱️ 處理耗時**: `{elapsed} 秒` | **⚡ 推理核心**: `{provider}`\n\n")
            
            f.write("### 📚 引用權威來源清單 (Top Citations)\n")
            if sources:
                for s in sources[:8]:
                    src = s.get("source", "未知")
                    page = s.get("page", 1)
                    score = s.get("score", 0.0)
                    url = s.get("url", "")
                    if url:
                        f.write(f"- [Score: `{score:.4f}`] **[{src}]({url})** (第 {page} 頁 / 官方網址: [{url}]({url}))\n")
                    else:
                        f.write(f"- [Score: `{score:.4f}`] **{src}** (第 {page} 頁)\n")
            else:
                f.write("- *(無檢索到相關文檔)*\n")
            f.write("\n")
            
            f.write("### 💡 專家系統生成解答 (Expert Answer)\n\n")
            f.write(answer.strip() + "\n\n")
            f.write("---\n\n")
            f.flush()
            
    print(f"\n🎉 12 題測試全數完成！完整報告已儲存至: {output_file}")

if __name__ == '__main__':
    main()
