import unittest
import vector_store

class TestExactCodeRetrieval(unittest.TestCase):
    def test_code_1059_exact_retrieval(self):
        """驗證 1059 代碼提問時，Rank 1 必須為 070842 事件表格"""
        q = "我的flashsystem 7200報了一個1059的錯誤該怎麼處理"
        chunks = vector_store.query_kb(q, top_k=5)
        self.assertGreater(len(chunks), 0)
        top1 = chunks[0]
        self.assertIn("1059", top1["content"])
        self.assertTrue("070842" in top1["content"] or "Fibre Channel" in top1["content"])
        self.assertEqual(top1["metadata"].get("code"), "1059")

    def test_model_number_no_false_alarm(self):
        """驗證 FlashSystem 機型編號 (如 7200, 5200) 不會被誤判為錯誤代碼"""
        q = "FlashSystem 5200 與 7200 的規格比較"
        chunks = vector_store.query_kb(q, top_k=3)
        for c in chunks:
            self.assertFalse(str(c["id"]).startswith("exact_code_event_"))

if __name__ == "__main__":
    unittest.main()
