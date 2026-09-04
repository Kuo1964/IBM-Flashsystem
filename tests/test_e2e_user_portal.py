"""
端到端使用者入口與審計日誌全流程驗證測試 (E2E User Portal & Audit Trail Test)
"""

import unittest
import sys
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

import web_app

class TestE2EUserPortal(unittest.TestCase):
    def test_e2e_flow(self):
        """測試 Auto-Provisioning 登入 ➔ 提問串流 ➔ 審計日誌寫入 ➔ 歷史會話調閱全流程"""
        client = TestClient(web_app.app)
        unique_id = int(time.time() * 1000)
        username = f"engineer_{unique_id}"
        password = "CharliePass2026!"
        session_id = f"sess_e2e_{unique_id}"

        # 1. 首次登入 (Auto-Provisioning)
        login_res = client.post("/api/auth/login", json={
            "username": username,
            "password": password
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn("token", data)
        token = data["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 提問並觸發串流與審計
        session_id = f"sess_e2e_{username}"
        query_text = "FS5030 Storage 網路 MTU 改成 9000 可以嗎？"
        stream_res = client.post(
            "/api/query/stream",
            json={"query": query_text, "top_k": 10, "session_id": session_id},
            headers=headers
        )
        self.assertEqual(stream_res.status_code, 200)
        self.assertIn("text/event-stream", stream_res.headers.get("content-type", ""))

        # 3. 調閱使用者歷史會話列表
        sessions_res = client.get("/api/sessions", headers=headers)
        self.assertEqual(sessions_res.status_code, 200)
        sessions = sessions_res.json().get("sessions", [])
        self.assertTrue(len(sessions) > 0)
        self.assertEqual(sessions[0]["session_id"], session_id)

        # 4. 調閱該會話歷史問答與審計數據
        msg_res = client.get(f"/api/sessions/{session_id}/messages", headers=headers)
        self.assertEqual(msg_res.status_code, 200)
        messages = msg_res.json().get("messages", [])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["query"], query_text)
        self.assertTrue("chportethernet" in messages[0]["answer"].lower() or "mtu" in messages[0]["answer"].lower())
        self.assertGreater(messages[0]["cost_twd"], 0.0)

if __name__ == "__main__":
    unittest.main()
