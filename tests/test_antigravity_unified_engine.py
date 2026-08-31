"""
TDD 測試套件：Antigravity 統一專家大腦生成引擎 (Antigravity Unified Response Engine)
驗證輸出風格與 Antigravity 保持 100% 一致：
1. 結構化 Emoji 分區 (🏛️ 部署、🌐 網路、🛠️ 安裝、💻 代碼、⚠️ 警告)
2. 零重複開場白與自我介紹 (次數 <= 1)
3. 官方紅皮書頁碼引述標籤
4. 精煉無廢話、篇幅適中且 100% 零截斷
"""
import unittest
import rag_core

class TestAntigravityUnifiedEngine(unittest.TestCase):

    def test_pbha_ip_quorum_antigravity_structure(self):
        query = "請給我一個PBHA IP Quorum設定的建議如果我的兩個FS5600系統放在兩個不同的site IP Quorum該怎麼設計"
        result = rag_core.RAGEngine.process_query(query, top_k=25)
        
        self.assertEqual(result.get("status"), "success", "查詢執行必須成功")
        answer = result.get("answer", "")
        self.assertGreater(len(answer), 500, "回答長度不可過短")
        self.assertLess(len(answer), 4000, f"回答篇幅應精煉適中 (目前 {len(answer)} 字元，不應超過 4000 字元膨脹)")

        # 1. 驗證結構化 Emoji 三大區塊
        self.assertTrue("🏛️" in answer or "一、" in answer, "必須包含第一章部署架構區塊")
        self.assertTrue("🌐" in answer or "二、" in answer, "必須包含第二章網路通訊區塊")
        self.assertTrue("🛠️" in answer or "三、" in answer, "必須包含第三章安裝與安全規範區塊")

        # 2. 驗證零重複開場白
        greeting_count = answer.count("好的，客戶您好") + answer.count("我是您的") + answer.count("我是 IBM Storage")
        self.assertLessEqual(greeting_count, 1, f"開場白與自我介紹不可重複出現 (目前出現 {greeting_count} 次)")

        # 3. 驗證官方出處標籤
        self.assertTrue("[來源:" in answer, "必須包含官方文檔頁碼出處標籤")

        # 4. 驗證核心技術參數完整性
        self.assertTrue("1260" in answer, "必須包含 TCP 1260 埠號")
        self.assertTrue("80" in answer, "必須包含 80ms 延遲上限")

    def test_cli_service_ip_antigravity_structure(self):
        query = "如何修改 node 的 service ip"
        result = rag_core.RAGEngine.process_query(query, top_k=25)
        
        self.assertEqual(result.get("status"), "success", "查詢執行必須成功")
        answer = result.get("answer", "")
        
        # 1. 驗證包含置頂程式碼區塊與正確命令
        self.assertTrue("```bash" in answer or "```" in answer, "必須包含 CLI 程式碼區塊")
        self.assertTrue(any(cmd in answer for cmd in ["chserviceip", "chnodeserviceip", "chnodeip"]), "必須包含正確的 Node IP 修改指令")


        
        # 2. 驗證包含安全警告與參數
        self.assertTrue("⚠️" in answer or "警告" in answer or "注意" in answer, "必須包含安全注意事項")
        self.assertTrue("-serviceip" in answer or "參數" in answer, "必須包含指令參數說明")

if __name__ == "__main__":
    unittest.main()
