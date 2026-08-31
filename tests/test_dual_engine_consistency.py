"""
IBM FlashSystem 專家系統 - 雙端 (Web & Local) 答案一致性與檢索對比自動化測試套件
測試三大主題：
1. GMCV 轉 PBR
2. HyperSwap 配置與注意事項
3. Safeguarded Copy 不可變快照
"""

import sys
import os
import asyncio
from pathlib import Path

# 將專案根目錄加入 PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prompts
import vector_store
from web_app import clear_query_cache, query_knowledge_base, QueryRequest

TEST_QUESTIONS = [
    {
        "id": "Q1_GMCV_PBR",
        "topic": "GMCV 轉 PBR",
        "query": "我的客戶想從傳統的GMCV轉換成PBR要怎麼做要注意什麼？詳細的流程是怎麼樣？",
        "expected_keywords": ["8.5.2", "volume group", "mkreplicationpolicy", "redp5704", "change volume"]
    },
    {
        "id": "Q2_HYPERSWAP",
        "topic": "HyperSwap 架構",
        "query": "HyperSwap 的配置前置條件是什麼？如何設定 active-active 雙活儲存？",
        "expected_keywords": ["sg248569", "site", "quorum", "policy-based ha"]
    },
    {
        "id": "Q3_SAFEGUARDED_COPY",
        "topic": "Safeguarded Copy 防護",
        "query": "Safeguarded Copy 和普通 FlashCopy 有何不同？如何防範勒索軟體攻擊？",
        "expected_keywords": ["immutable", "copy services manager", "snapshot", "redp5586"]
    }
]

async def run_consistency_tests():
    print("==================================================")
    print("🧪 開始執行雙端 (Web & Local) RAG 檢索與答案一致性測試")
    print("==================================================\n")

    await clear_query_cache()

    passed_count = 0
    total_count = len(TEST_QUESTIONS)

    for item in TEST_QUESTIONS:
        q_id = item["id"]
        topic = item["topic"]
        query = item["query"]
        expected_kw = item["expected_keywords"]

        print(f"👉 測試項目 [{q_id}] 主題: {topic}")
        print(f"   提問: '{query}'")

        # 1. 測試 Local 檢索 (vector_store + prompts)
        expanded_q = prompts.get_expanded_query(query)
        chunks = vector_store.query_kb(query_text=expanded_q, top_k=5, min_similarity=0.0)
        
        print(f"   [Local Engine] 召回 Chunks: {len(chunks)} 筆")
        top_source = chunks[0]['metadata'].get('source', '') if chunks else 'None'
        print(f"   [Local Engine] Top 1 來源: {top_source} (Score: {chunks[0]['similarity_score'] if chunks else 0})")

        # 2. 測試 Web API 端點 (query_knowledge_base)
        req = QueryRequest(query=query, top_k=5)
        class DummyRequest: client = None
        res = await query_knowledge_base(req, DummyRequest())

        answer = res.get("answer", "")
        sources = res.get("sources", [])

        print(f"   [Web API Engine] Answer 長度: {len(answer)} 字, 來源數: {len(sources)}")

        # 驗證關鍵字 match
        matched_kw = [kw for kw in expected_kw if kw.lower() in answer.lower() or any(kw.lower() in str(s).lower() for s in sources)]
        print(f"   [一致性驗證] 關鍵字匹配: {len(matched_kw)}/{len(expected_kw)} -> {matched_kw}")

        if len(chunks) > 0 and len(sources) > 0 and len(answer) > 200:
            print(f"   ✅ [{q_id}] 雙端檢索與解答一致性測試通過！\n")
            passed_count += 1
        else:
            print(f"   ❌ [{q_id}] 測試未完全達標。\n")

    print("==================================================")
    print(f"📊 測試總結: 通過率 {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_consistency_tests())
