# -*- coding: utf-8 -*-
"""
自動化測試：多詞向量召回 (Multi-Query Retrieval) 與 FS5200 SAS 介面卡/Node Canister 圖解問答
"""

import sys
from pathlib import Path

# 將隔離目錄加入模組路徑
CURRENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CURRENT_DIR))

import vector_store
import rag_core

def test_multi_query_vector_retrieval():
    """測試向量庫是否能透過 expanded_terms 成功召回 sg248520.pdf (FS5200)"""
    query = "S5200 SAS adapter是額外插卡嗎還是內建的？給我看一下 node canister 的圖"
    expanded_terms = ["FlashSystem 5200", "12 Gbps SAS adapter", "PCIe adapter slot", "node canister"]
    
    chunks = vector_store.query_kb(
        query_text=query,
        top_k=10,
        expanded_terms=expanded_terms
    )
    
    assert len(chunks) > 0, "檢索結果不應為空"
    sources = [c["metadata"].get("source", "") for c in chunks]
    print(f"召回的來源文檔: {set(sources)}")
    
    has_fs5200_doc = any("sg248520" in s.lower() or "5200" in s.lower() for s in sources)
    print(f"是否成功命中 FlashSystem 5200 官方紅皮書: {has_fs5200_doc}")
    assert has_fs5200_doc, "必須成功召回 sg248520 (FlashSystem 5200 原廠文檔)"

def test_full_rag_inference():
    """測試完整 RAG 端到端推理結果"""
    query = "S5200 SAS adapter是額外插卡嗎還是內建的？給我看一下 node canister 的圖"
    res = rag_core.process_query(query, top_k=15)
    
    print("\n=== RAG 推理結果 ===")
    print(f"狀態: {res.get('status')}")
    print(f"意圖分類: {res.get('intent')}")
    print(f"推理解答模型/模組: {res.get('provider')}")
    print(f"召回 Chunks 筆數: {res.get('chunks_count')}")
    print(f"耗時: {res.get('execution_time_seconds')} 秒")
    print(f"解答預覽:\n{res.get('answer')[:300]}...\n")
    
    answer = res.get("answer", "")
    assert "插卡" in answer or "pcie" in answer.lower() or "選購" in answer, "解答中應明確提及插卡/PCIe/選購"
    assert "![" in answer, "解答中應包含圖片 Markdown 標記"

if __name__ == "__main__":
    print("開始執行多詞向量檢索測試...")
    test_multi_query_vector_retrieval()
    print("向量檢索測試通過！\n")
    
    print("開始執行端到端 RAG 推理測試...")
    test_full_rag_inference()
    print("端到端 RAG 推理測試通過！")
