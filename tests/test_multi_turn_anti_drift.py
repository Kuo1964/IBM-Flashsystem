"""
Smart Context Isolation 智慧多輪防失焦測試 (Ticket 03 Test)
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import rag_core

class TestMultiTurnAntiDrift(unittest.TestCase):
    def test_01_multi_turn_anti_drift_topic_switching(self):
        """測試第 1 題問 NDVM ➔ 第 2 題切換問 MTU 9000 時，第 2 題零 NDVM 舊手冊干擾"""
        # 模擬第 1 輪對話純文字歷史
        chat_history = [
            {"role": "user", "content": "如何使用 NDVM 技術將一個在線提供 I/O 的磁區遷移？"},
            {"role": "assistant", "content": "可以使用 Storage Virtualize 8.4.2+ 的 Volume Mobility 與 mkpartnership、mkrcrelationship -migration 指令進行無中斷遷移。"}
        ]
        
        # 第 2 輪提問切換為 MTU
        query_2 = "FS5030 iSCSI MTU 想從 1500 改為 9000 可以嗎？"
        res = rag_core.RAGEngine.process_query(query_2, top_k=20, chat_history=chat_history)
        
        self.assertEqual(res["status"], "success")
        ans_lower = res["answer"].lower()
        
        # 驗證第 2 題核心答案精準聚焦於 chportethernet 與 MTU
        self.assertTrue("chportethernet" in ans_lower or "mtu" in ans_lower)
        # 驗證絕不把第 1 題的 NDVM 誤當作第 2 題的實施方式
        self.assertNotIn("mkrcrelationship -migration", ans_lower)

if __name__ == "__main__":
    unittest.main()
