"""
MTU 與指令生命週期防護單元測試 (MTU & chportethernet Lifecycle Guardrail)
驗證：
1. 舊版廢棄指令 chnodeip 會被 GroundingAuditor 嚴格攔截並自動修正為 chportethernet。
2. 現代官方指令 chportethernet 為合法白名單指令。
3. 提問 MTU 9000 時，檢索前置白名單精確命中 chportethernet。
"""

import unittest
from grounding_auditor import GroundingAuditor
import vector_store

class TestMTULifecycleGuardrail(unittest.TestCase):
    def setUp(self):
        self.auditor = GroundingAuditor()

    def test_01_chnodeip_is_intercepted_and_corrected(self):
        """測試 chnodeip 被標記為廢棄指令並提供 chportethernet 官方對照"""
        draft = "請在終端機執行 chnodeip -mtu 9000 -port 1 node1 進行修改。"
        res = self.auditor.audit_response("如何修改 MTU", draft)
        
        self.assertFalse(res["passed"], "使用 chnodeip 必須無法通過審計")
        self.assertTrue(len(res["hallucinations"]) > 0)
        
        # 驗證糾錯映射指向 chportethernet
        corrected = False
        for h in res["hallucinations"]:
            if h.get("invalid_command") == "chnodeip" and "chportethernet" in h.get("real_command", ""):
                corrected = True
                break
        self.assertTrue(corrected, "chnodeip 必須自動被映射並糾錯為 chportethernet")

    def test_02_chportethernet_passes_audit(self):
        """測試現代官方指令 chportethernet 正常通過審計"""
        draft = "請在終端機執行 chportethernet -mtu 9000 1 進行修改，並使用 lsportethernet 驗證。"
        res = self.auditor.audit_response("如何修改 MTU", draft)
        self.assertTrue(res["passed"], "使用現代官方標準 chportethernet 必須 100% 通過審計")

    def test_03_mtu_retrieval_recalls_chportethernet(self):
        """測試提問 MTU 時前置白名單命中 chportethernet"""
        query = "FS5030 iSCSI 網路 MTU 1500 改成 9000 該使用什麼指令"
        chunks = vector_store.query_kb(query, top_k=10)
        
        all_text = " ".join([c["content"] for c in chunks])
        self.assertIn("chportethernet", all_text, "檢索上下文必須包含官方指令 chportethernet")

if __name__ == "__main__":
    unittest.main()
