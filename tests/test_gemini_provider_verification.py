"""
Google Gemini 專家大腦模型調用真確性與反覆驗證測試
驗證：
1. 核心流水線的解答 100% 源自 Google Gemini (gemini-2.5-flash) API
2. 絕不調用本地 Ollama 降級
3. 反覆執行多個不同領域問答（CLI、故障碼、架構比較、MTU），確保每一次的 Provider 皆為 Google Gemini
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import rag_core

class TestGeminiProviderVerification(unittest.TestCase):
    def test_gemini_api_key_configured(self):
        """驗證系統環境已正確配置 Google Gemini API Key"""
        self.assertTrue(bool(config.GEMINI_API_KEY), "GEMINI_API_KEY 未配置！")
        self.assertEqual(config.LLM_PROVIDER, "gemini")
        self.assertEqual(config.GEMINI_MODEL, "gemini-2.5-flash")

    def test_repeated_gemini_calls(self):
        """反覆驗證多個問答請求，100% 由 Google Gemini 專家大模型處理"""
        test_queries = [
            ("FS5030 iSCSI MTU 9000 指令", "CLI 指令與 MTU"),
            ("FS7300 error code 1474", "電池故障排查"),
            ("比較 FCM4 與 FCM5 的差異", "硬體規格比較"),
            ("如何使用 NDVM 進行跨 I/O Group 磁區遷移？", "NDVM 架構遷移")
        ]

        for idx, (query, desc) in enumerate(test_queries, 1):
            print(f"\n[驗證輪次 {idx}/4] 測試題目: '{query}' ({desc})")
            res = rag_core.RAGEngine.process_query(query, top_k=15)
            
            self.assertEqual(res["status"], "success")
            provider = res.get("provider", "")
            print(f"  ➔ 模型供應商 (Provider): {provider}")
            print(f"  ➔ 解答長度: {len(res.get('answer', ''))} 字元")
            print(f"  ➔ 引用來源筆數: {len(res.get('sources', []))} 筆")
            
            # 斷言：必須為 Google Gemini，絕對不可為本地 Ollama
            self.assertIn("Google Gemini", provider, f"第 {idx} 輪問答未經由 Gemini API 處理！")
            self.assertNotIn("Ollama", provider, f"第 {idx} 輪問答誤降級至本地 Ollama！")
            self.assertTrue(len(res.get("answer", "")) > 100, "解答字數過短，非完整大模型生成！")

if __name__ == "__main__":
    unittest.main()
