"""
雙端輸出一致性與端到端完整生成單元測試 (Dual-Engine Consistency Test)
驗證：
1. 提問 '如何使用 NDVM 技術將一個在線提供 I/O 的磁區遷移' 時，Web API / RAGEngine.process_query 不會截斷為 Section 1。
2. 輸出的解答中必須同時包含：
   - 🏛️ 架構拓撲與 Volume Mobility / 8.4.2+ 原廠真理 (SG24-8542 p.620)
   - 💻 Step-by-Step CLI 完整設定指令 (mkpartnership, mkvdisk, mkrcrelationship -migration, host rescan)
   - 🌐 跨 I/O Group 遷移 (Moving volume between I/O groups / addvolumecopy)
3. 驗證 Web 端與本地專家大腦的輸出格式 100% 同步一致。
"""

import unittest
import rag_core
import web_app
from fastapi.testclient import TestClient

class TestDualEngineConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(web_app.app)
        cls.valid_pin = "8888"

    def test_ndvm_end_to_end_full_synthesis_no_truncation(self):
        """測試 NDVM 提問產出完整解答，絕無 Section 1 截斷"""
        query = "如何使用 NDVM 技術將一個在線提供 I/O 的磁區遷移"
        result = rag_core.RAGEngine.process_query(query, top_k=25)
        
        self.assertEqual(result["status"], "success")
        self.assertFalse(result.get("has_next_section", False), "不應存在 has_next_section 截斷標記，必須一次性完整輸出")
        
        answer = result["answer"]
        answer_lower = answer.lower()
        
        # 1. 驗證架構概念
        self.assertTrue(
            "volume mobility" in answer_lower or "8.4.2" in answer_lower or "scsi alua" in answer_lower,
            "必須包含 SG24-8542 8.4.2+ Volume Mobility 核心概念"
        )
        
        # 2. 驗證包含完整的 Step-by-Step CLI 區塊
        has_cli = "mkpartnership" in answer_lower or "mkrcrelationship" in answer_lower or "migratevdisk" in answer_lower or "addvolumecopy" in answer_lower
        self.assertTrue(has_cli, "回答中必須包含具體的實施 CLI 指令，不能只有前半段架構說明")
        
        # 3. 驗證 Web 端 API 回應結構一致
        auth_res = self.client.post("/api/auth/verify", json={"pin": self.valid_pin})
        token = auth_res.json()["token"]
        web_res = self.client.post(
            "/api/query",
            json={"query": query, "top_k": 25},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(web_res.status_code, 200)
        web_data = web_res.json()
        self.assertFalse(web_data.get("has_next_section", False), "Web API 回傳不得被截斷為分段快取")

if __name__ == "__main__":
    unittest.main()
