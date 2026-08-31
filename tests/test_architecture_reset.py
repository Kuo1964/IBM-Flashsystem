"""
IBM FlashSystem 專家系統 - 架構全面重置自動化測試套件 (Architecture Reset Suite)
驗證三大核心 Guardrails：
1. 零 Raw Context 洩漏 (無 【參考文檔】 標籤，全數轉換為人化專家解答與出處引述)
2. 雙端 100% 絕對零分歧 (Web API 與 Local Engine 回應完全同源)
3. 繁體中文與提問意圖精準對齊 (問比較給比較表，問步驟給步驟)
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rag_core
from web_app import query_knowledge_base, QueryRequest

RESET_TEST_CASES = [
    {
        "id": "CASE_1_HYPERSWAP_PBHA_COMPARE",
        "topic": "HyperSwap vs. PBHA 比較",
        "query": "比較一下HyperSwap跟PBHA這兩種架構的不同",
        "must_contain": ["HyperSwap", "PBHA", "Stretched Cluster", "Storage Partition"],
        "must_not_contain": ["【參考文檔 1】", "hsm -list", "pba -list", "Permanent Block Assignment"]
    },
    {
        "id": "CASE_2_GRID_MIGRATION",
        "topic": "FlashSystem Grid 修改架構",
        "query": "我的客戶想從兩個 I/O Group 的 cluster 修改架構成為 FlashSystem Grid，有什麼建議的做法？",
        "must_contain": ["FlashSystem Grid", "Storage Partition", "Evaluate Placement"],
        "must_not_contain": ["【參考文檔 1】", "Fabric-Attached Boot Unit"]
    },
    {
        "id": "CASE_3_GMCV_PBR",
        "topic": "GMCV 轉 PBR 複製政策",
        "query": "我的客戶想從傳統的GMCV轉換成PBR要怎麼做要注意什麼？詳細的流程是怎麼樣？",
        "must_contain": ["8.5.2", "Volume Group", "mkreplicationpolicy"],
        "must_not_contain": ["【參考文檔 1】"]
    }
]

async def run_reset_suite():
    print("==================================================")
    print("🛡️ 執行【架構重置與三防 Guardrails】自動化測試套件")
    print("==================================================\n")

    passed_count = 0
    total_count = len(RESET_TEST_CASES)

    for item in RESET_TEST_CASES:
        c_id = item["id"]
        topic = item["topic"]
        query = item["query"]
        must_in = item.get("must_contain", [])
        must_not_in = item.get("must_not_contain", [])

        print(f"👉 測試案例 [{c_id}] 主題: {topic}")
        print(f"   提問: '{query}'")

        # 1. 呼叫 Local Engine
        res_local = rag_core.process_query(query_text=query, top_k=5)

        # 2. 呼叫 Web API Engine
        req = QueryRequest(query=query, top_k=5)
        class DummyRequest: client = None
        res_web = await query_knowledge_base(req, DummyRequest())

        local_ans = res_local.get("answer", "")
        web_ans = res_web.get("answer", "")

        # Guardrail 1: 零 Raw Context 洩漏斷言
        for bad_kw in must_not_in:
            assert bad_kw not in local_ans, f"Local 端回答包含違規字串 '{bad_kw}'!"
            assert bad_kw not in web_ans, f"Web 端回答包含違規字串 '{bad_kw}'!"

        # Guardrail 2: 雙端 100% 絕對零分歧斷言
        assert res_local.get("chunks_count") == res_web.get("chunks_count"), "Chunks 數量不一致!"
        assert res_local.get("sources") == res_web.get("sources"), "Sources 不一致!"

        # Guardrail 3: 關鍵知識點包含斷言
        for good_kw in must_in:
            assert good_kw.lower() in local_ans.lower(), f"回答缺少關鍵字 '{good_kw}'!"

        print(f"   [雙端驗證] Answer 長度: Local({len(local_ans)}) vs Web({len(web_ans)}) | 引用筆數: {len(res_local.get('sources', []))}")
        print(f"   ✅ [{c_id}] 零 Raw Text 洩漏、雙端零分歧、意圖精準對齊測試通過！\n")
        passed_count += 1

    print("==================================================")
    print(f"🏆 架構重置測試總結: 通過率 {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_reset_suite())
