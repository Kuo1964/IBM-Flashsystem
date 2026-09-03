"""
Audit Trail 審計引擎與歷史對話單元測試 (Ticket 02 Test)
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import audit_logger

class TestAuditLogger(unittest.TestCase):
    def test_01_log_conversation_and_retrieve_session(self):
        """測試問答審計記錄寫入與會話調閱"""
        import time
        user_id = 9999
        session_id = f"sess_test_{int(time.time()*1000)}"
        query = "如何使用 chportethernet 修改 MTU 為 9000？"
        answer = "請執行 chportethernet -mtu 9000 1 進行修改。"
        sources = [{"source": "9.1.0_svc_bkmap_cliguidebk.pdf", "page": 543}]
        
        log_id = audit_logger.log_conversation_turn(
            user_id=user_id,
            session_id=session_id,
            query_text=query,
            answer_text=answer,
            sources=sources,
            response_time_seconds=1.25,
            provider="Google Gemini (gemini-2.5-flash)"
        )
        self.assertGreater(log_id, 0)
        
        # 查詢使用者會話清單
        sessions = audit_logger.get_user_sessions(user_id)
        self.assertTrue(len(sessions) > 0)
        self.assertEqual(sessions[0]["session_id"], session_id)
        
        # 查詢會話訊息
        messages = audit_logger.get_session_messages(session_id, user_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["query"], query)
        self.assertEqual(messages[0]["answer"], answer)
        self.assertEqual(len(messages[0]["sources"]), 1)
        self.assertGreater(messages[0]["cost_twd"], 0.0)

if __name__ == "__main__":
    unittest.main()
