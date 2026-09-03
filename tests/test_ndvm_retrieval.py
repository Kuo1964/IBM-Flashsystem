"""
NDVM 與 Volume Mobility 原廠真理檢索單元測試 (unittest 標準版)
"""

import unittest
import vector_store

class TestNDVMRetrieval(unittest.TestCase):
    def test_ndvm_retrieval_recalls_sg248542_and_web(self):
        query = "如何使用 NDVM 技術將一個在線提供 I/O 的磁區遷移"
        results = vector_store.query_kb(query_text=query, top_k=25, min_similarity=0.0)
        
        self.assertTrue(len(results) > 0, "檢索結果不應為空")
        
        sources = [item["metadata"].get("source", "") for item in results]
        pages = [item["metadata"].get("page") for item in results]
        docs = [item["content"] for item in results]
        
        # 1. 驗證是否召回 SG248542 p.620~622
        has_sg248542_p620 = any(
            "sg248542" in str(s).lower() and p in [620, 621, 622]
            for s, p in zip(sources, pages)
        )
        self.assertTrue(has_sg248542_p620, "必須精準召回 SG24-8542 第 620~622 頁之 Volume Mobility 章節")
        
        # 2. 驗證是否召回 Moving a volume between I/O groups 官方頁面
        has_moving_iogrp_web = any(
            "moving a volume between i/o groups" in str(item["metadata"].get("source", "")).lower() or "moving-volume-between-io-groups" in str(item["metadata"].get("url", "")).lower()
            for item in results
        )
        self.assertTrue(has_moving_iogrp_web, "必須精準召回 Moving a volume between I/O groups 官方網頁")
        
        # 3. 驗證內容關鍵字
        all_text = " ".join(docs)
        self.assertTrue("nondisruptively" in all_text.lower() or "non-disruptive" in all_text.lower())
        self.assertTrue("alua" in all_text.lower() or "i/o group" in all_text.lower())

if __name__ == "__main__":
    unittest.main()
