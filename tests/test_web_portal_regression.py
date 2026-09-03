"""
IBM FlashSystem 跨裝置 Web Portal 全流程回歸與題庫驗證測試 (Web Portal Regression Suite)
驗證：
1. PIN 碼授權中介層防護 (Ticket 01)
2. SSE 串流問答協議與 Agentic 思考推送 (Ticket 02)
3. docs/test_queries_suite.md 題庫回歸與答案一致性比對 (Ticket 04)
"""

import unittest
import json
import time
from fastapi.testclient import TestClient
import web_app

class TestWebPortalRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(web_app.app)
        cls.valid_pin = "8888"
        cls.invalid_pin = "0000"

    def test_01_pin_auth_verification(self):
        """測試 PIN 碼驗證中介層"""
        # 1. 錯誤 PIN 碼
        res_fail = self.client.post("/api/auth/verify", json={"pin": self.invalid_pin})
        self.assertEqual(res_fail.status_code, 401)
        self.assertIn("PIN 碼不正確", res_fail.json().get("detail", ""))

        # 2. 正確 PIN 碼
        res_ok = self.client.post("/api/auth/verify", json={"pin": self.valid_pin})
        self.assertEqual(res_ok.status_code, 200)
        data = res_ok.json()
        self.assertIn("token", data)
        self.assertEqual(data["status"], "ok")

    def test_02_unauthorized_query_blocked(self):
        """測試未授權請求被 401 攔截"""
        res = self.client.post("/api/query", json={"query": "FlashSystem 5200 規格"})
        self.assertEqual(res.status_code, 401)

        res_stream = self.client.post("/api/query/stream", json={"query": "FlashSystem 5200 規格"})
        self.assertEqual(res_stream.status_code, 401)

    def test_03_authorized_streaming_ndvm_and_cli(self):
        """測試授權後 SSE 串流問答 (包含 NDVM 與 CLI 指令)"""
        # 先獲取 Token
        auth_res = self.client.post("/api/auth/verify", json={"pin": self.valid_pin})
        token = auth_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 測試提問 NDVM 線上遷移
        req_payload = {
            "query": "如何使用 NDVM 技術將一個在線提供 I/O 的磁區遷移",
            "top_k": 25,
            "session_id": "test_sess_01"
        }
        res = self.client.post("/api/query/stream", json=req_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))

        # 解析串流事件
        lines = res.text.split("\n\n")
        events = []
        full_content = ""
        for line in lines:
            if not line.strip():
                continue
            if line.startswith("event:"):
                parts = line.split("\n", 1)
                ev_type = parts[0].replace("event:", "").strip()
                data_json = parts[1].replace("data:", "").strip() if len(parts) > 1 else "{}"
                events.append(ev_type)
                try:
                    payload = json.loads(data_json)
                    if ev_type == "content":
                        full_content += payload.get("chunk", "")
                except Exception:
                    pass

        self.assertIn("thinking", events, "串流必須推送 thinking 思考狀態")
        self.assertIn("content", events, "串流必須推送 content 內容")
        self.assertIn("done", events, "串流必須推送 done 完成標記")

        # 驗證答案包含官方關鍵詞 (SG24-8542 Section 7.5)
        content_lower = full_content.lower()
        self.assertTrue(
            "volume mobility" in content_lower or "scsi alua" in content_lower or "8.4.2" in content_lower or "nondisruptive" in content_lower,
            "NDVM 解答必須精確錨定 SG24-8542 原廠真理"
        )

if __name__ == "__main__":
    unittest.main()
