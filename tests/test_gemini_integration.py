"""
單元與整合測試：驗證中央 RAG Engine 的 Google Gemini API 整合與自動降級機制
"""

import unittest
from unittest.mock import patch, MagicMock
import rag_core
import config

class TestGeminiIntegration(unittest.TestCase):

    def test_empty_query(self):
        """測試空查詢防護"""
        res = rag_core.process_query("")
        self.assertEqual(res["answer"], "提問內容不能為空")

    @patch("rag_core.vector_store.query_kb")
    @patch("rag_core.httpx.Client")
    def test_gemini_success_flow(self, mock_client_cls, mock_query_kb):
        """測試成功呼叫 Gemini API 流程"""
        # Mock 檢索結果
        mock_query_kb.return_value = [
            {
                "content": "FlashSystem 5600 支援 24 顆 NVMe FCM 磁碟，具備 10/25GbE 網路埠。",
                "metadata": {"source": "fs5600_guide", "page": 10, "type": "text"},
                "similarity_score": 0.85
            }
        ]

        # Mock Gemini 回應
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "### FlashSystem 5600 規格摘要\n- 支援 24 顆 FCM\n- 10/25GbE 連線"}]
                    }
                }
            ]
        }

        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value.__enter__.return_value = mock_client

        with patch.object(config, "GEMINI_API_KEY", "test-key-123"):
            res = rag_core.process_query("FlashSystem 5600 規格", top_k=3)
            self.assertIn("FlashSystem 5600 規格摘要", res["answer"])
            self.assertIn("Google Gemini", res["provider"])
            self.assertEqual(len(res["sources"]), 1)

    @patch("rag_core.vector_store.query_kb")
    @patch("rag_core.httpx.Client")
    def test_gemini_fallback_to_ollama(self, mock_client_cls, mock_query_kb):
        """測試 Gemini 失敗時自動降級至本地 Ollama"""
        mock_query_kb.return_value = [
            {
                "content": "FlashSystem 5600 支援 24 顆 NVMe FCM 磁碟。",
                "metadata": {"source": "fs5600_guide", "page": 10, "type": "text"},
                "similarity_score": 0.85
            }
        ]

        # 模擬 Gemini 拋出例外，但 Ollama 成功
        def mock_post_side_effect(url, **kwargs):
            mock_resp = MagicMock()
            if "googleapis.com" in url:
                mock_resp.status_code = 500
            else:
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"response": "這是來自本地 Ollama 的技術解答。FlashSystem 5600 具備完整 10/25GbE 網路埠與 NVMe FCM 磁碟支援，提供企業級高可用性虛擬化功能。"}
            return mock_resp

        mock_client = MagicMock()
        mock_client.post.side_effect = mock_post_side_effect
        mock_client_cls.return_value.__enter__.return_value = mock_client

        with patch.object(config, "GEMINI_API_KEY", "test-key-123"):
            res = rag_core.process_query("FlashSystem 5600 規格", top_k=3)
            self.assertIn("本地 Ollama", res["provider"])
            self.assertIn("這是來自本地 Ollama 的技術解答", res["answer"])

if __name__ == "__main__":
    unittest.main()
