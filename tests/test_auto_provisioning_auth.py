"""
Auto-Provisioning 認證與會話隔離單元測試 (Ticket 01 Test)
"""

import unittest
import sys
from pathlib import Path

# 將當前工作目錄加入路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import auth

class TestAutoProvisioningAuth(unittest.TestCase):
    def test_01_auto_provision_new_user(self):
        """測試新同仁首次登入自動建檔 (Auto-Provisioning)"""
        username = "engineer_alice_99"
        password = "SecurePassword123!"
        
        res = auth.authenticate_or_provision_user(username, password)
        self.assertEqual(res["status"], "success")
        self.assertIn("token", res)
        self.assertEqual(res["user"]["username"], username)
        
        # 驗證 Token 解密資訊
        payload = auth.verify_jwt_token(res["token"])
        self.assertIsNotNone(payload)
        self.assertEqual(payload["username"], username)

    def test_02_existing_user_login_and_wrong_password(self):
        """測試既有同仁登入與密碼錯誤防護"""
        username = "engineer_bob_88"
        password = "CorrectPassword123"
        
        # 首次建立
        auth.authenticate_or_provision_user(username, password)
        
        # 正確密碼再次登入
        res_ok = auth.authenticate_or_provision_user(username, password)
        self.assertEqual(res_ok["status"], "success")
        
        # 錯誤密碼拒絕
        with self.assertRaises(ValueError):
            auth.authenticate_or_provision_user(username, "WrongPassword")

if __name__ == "__main__":
    unittest.main()
