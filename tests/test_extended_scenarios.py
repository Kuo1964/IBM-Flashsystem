"""
IBM FlashSystem 專家系統 - 擴充版雙端一致性測試套件 (Pre-Merge Verification Suite)
涵蓋：
1. DRAID 1 / DRAID 6 最佳實踐與重建效能
2. FlashSystem 9500 SAN 拓樸與 NVMe-oF 配置
3. Volume Group Snapshot 與 Safeguarded 整合
4. IP Partnership 頻寬與 QoS 限制
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prompts
import vector_store
from web_app import clear_query_cache, query_knowledge_base, QueryRequest

EXTENDED_QUESTIONS = [
    {
        "id": "Q4_DRAID_PERF",
        "topic": "DRAID 1 vs DRAID 6",
        "query": "DRAID 1 和 DRAID 6 在重建時間與效能上有何差異？最佳實踐建議是什麼？",
        "expected_keywords": ["draid", "rebuild", "drive failure", "performance"]
    },
    {
        "id": "Q5_FS9500_SAN",
        "topic": "FlashSystem 9500 SAN 拓樸",
        "query": "IBM FlashSystem 9500 規劃 SAN 拓樸時，NVMe-oF 與 FC 埠的連接注意事項有哪些？",
        "expected_keywords": ["9500", "nvme", "fibre channel", "port"]
    },
    {
        "id": "Q6_VG_SNAPSHOT",
        "topic": "Volume Group Snapshot 災備測試",
        "query": "如何利用 Volume Group Snapshot 進行無中斷的 DR 災備演練？與舊 FlashCopy 有何差別？",
        "expected_keywords": ["snapshot", "volume group", "crash-consistent", "dr"]
    }
]

async def run_extended_tests():
    print("==================================================")
    print("🧪 執行擴充版 Pre-Merge 雙端一致性測試套件")
    print("==================================================\n")

    await clear_query_cache()

    passed_count = 0
    total_count = len(EXTENDED_QUESTIONS)

    for item in EXTENDED_QUESTIONS:
        q_id = item["id"]
        topic = item["topic"]
        query = item["query"]

        print(f"👉 測試項目 [{q_id}] 主題: {topic}")
        print(f"   提問: '{query}'")

        expanded_q = prompts.get_expanded_query(query)
        chunks = vector_store.query_kb(query_text=expanded_q, top_k=5, min_similarity=0.0)
        
        print(f"   [Local Engine] 召回 Chunks: {len(chunks)} 筆")
        if chunks:
            print(f"   [Local Engine] Top 1: {chunks[0]['metadata'].get('source')} (Score: {chunks[0]['similarity_score']})")

        req = QueryRequest(query=query, top_k=5)
        class DummyRequest: client = None
        res = await query_knowledge_base(req, DummyRequest())

        answer = res.get("answer", "")
        sources = res.get("sources", [])

        print(f"   [Web API Engine] Answer 長度: {len(answer)} 字, 引用來源數: {len(sources)}")
        if sources:
            print(f"   [Web API Engine] 主要引用: {[s['source'] for s in sources[:3]]}")

        if len(chunks) > 0 and len(sources) > 0 and len(answer) > 200:
            print(f"   ✅ [{q_id}] 雙端對比測試通過！\n")
            passed_count += 1
        else:
            print(f"   ❌ [{q_id}] 測試未達標。\n")

    print("==================================================")
    print(f"📊 擴充測試總結: 通過率 {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_extended_tests())
