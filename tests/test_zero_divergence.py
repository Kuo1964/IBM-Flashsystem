"""
IBM FlashSystem 專家系統 - 零差別百分百一致性測試套件 (Zero-Divergence Suite)
測試目標：
驗證不論從 Web API 介面還是 Local CLI / Python 發送完全相同的問題，
系統內部調用的處理邏輯、召回的 Chunks、引用來源頁碼以及產出的解答 100% 絕對完全一致！
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rag_core
from web_app import clear_query_cache, query_knowledge_base, QueryRequest

ZERO_DIVERGENCE_TEST_CASES = [
    {
        "id": "CASE_1_GRID",
        "topic": "FlashSystem Grid 修改架構",
        "query": "我的客戶想從兩個 I/O Group 的 cluster 修改架構成為 FlashSystem Grid，有什麼建議的做法？"
    },
    {
        "id": "CASE_2_GMCV_PBR",
        "topic": "GMCV 轉 PBR",
        "query": "我的客戶想從傳統的GMCV轉換成PBR要怎麼做要注意什麼？詳細的流程是怎麼樣？"
    },
    {
        "id": "CASE_3_HYPERSWAP",
        "topic": "HyperSwap 雙活架構",
        "query": "HyperSwap 的配置前置條件是什麼？如何設定 active-active 雙活儲存？"
    },
    {
        "id": "CASE_4_SAFEGUARDED",
        "topic": "Safeguarded Copy 防護",
        "query": "Safeguarded Copy 和普通 FlashCopy 有何不同？如何防範勒索軟體攻擊？"
    }
]

async def run_zero_divergence_suite():
    print("==================================================")
    print("🎯 執行【零差別百分百一致性 (Zero-Divergence)】自動化測試")
    print("==================================================\n")

    await clear_query_cache()

    passed_count = 0
    total_count = len(ZERO_DIVERGENCE_TEST_CASES)

    for item in ZERO_DIVERGENCE_TEST_CASES:
        c_id = item["id"]
        topic = item["topic"]
        query = item["query"]

        print(f"👉 測試案例 [{c_id}] 主題: {topic}")
        print(f"   提問: '{query}'")

        # 1. 執行 Local Central Engine (rag_core)
        res_local = rag_core.process_query(query_text=query, top_k=5)

        # 2. 執行 Web API Engine (web_app)
        req = QueryRequest(query=query, top_k=5)
        class DummyRequest: client = None
        res_web = await query_knowledge_base(req, DummyRequest())

        # 3. 雙端 100% 絕對零差別斷言 (Strict Zero-Divergence Assertions)
        local_chunks_count = res_local.get("chunks_count")
        web_chunks_count = res_web.get("chunks_count")

        local_sources = [(s["source"], s["page"]) for s in res_local.get("sources", [])]
        web_sources = [(s["source"], s["page"]) for s in res_web.get("sources", [])]

        local_ans = res_local.get("answer", "").strip()
        web_ans = res_web.get("answer", "").strip()

        print(f"   [Local 核心] Chunks: {local_chunks_count}, Sources: {local_sources[:2]}")
        print(f"   [Web API  ] Chunks: {web_chunks_count}, Sources: {web_sources[:2]}")

        # 斷言 1: Chunks 數量 100% 相同
        assert local_chunks_count == web_chunks_count, f"Chunks 數量不一致: Local({local_chunks_count}) vs Web({web_chunks_count})"

        # 斷言 2: 引用的來源與頁碼 100% 相同
        assert local_sources == web_sources, f"引用來源不一致: Local({local_sources}) vs Web({web_sources})"

        # 斷言 3: 生成解答內容 100% 相同
        assert local_ans == web_ans, f"產出解答不一致！"

        print(f"   ✅ [{c_id}] 雙端 JSON 數據與產出解答 100.0% 零差別對齊！\n")
        passed_count += 1

    print("==================================================")
    print(f"🏆 零差別測試總結: 通過率 {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_zero_divergence_suite())
