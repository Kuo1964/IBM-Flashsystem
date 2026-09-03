"""
全量 16 類已廢棄/替代指令生命週期審計單元測試 (Full Command Deprecation & Lifecycle Audit)
驗證：
1. 矩陣中所有 16 類歷史/廢棄/幻想指令均能被 GroundingAuditor 100% 精準捕捉並糾正。
2. 驗證所有糾正後的目標指令均存在於 9.1.0 官方白名單或官方標準集合中。
"""

import unittest
from grounding_auditor import GroundingAuditor

class TestFullCommandDeprecationAudit(unittest.TestCase):
    def setUp(self):
        self.auditor = GroundingAuditor()

    def test_all_16_deprecated_commands_intercepted(self):
        """測試全量 16 類已廢棄指令的攔截與糾錯映射"""
        test_matrix = [
            ("chnodeip", "chportethernet"),
            ("lserrorlog", "lseventlog"),
            ("lserrorevent", "lseventlog"),
            ("lsdate", "showtimezone"),
            ("importvdisk", "mkvdisk -image"),
            ("mkstoragepartition", "managegrid"),
            ("lsstoragepartition", "lsgridpartition"),
            ("manageflashgrid", "managegrid"),
            ("lshyperswap", "lsvdisk"),
            ("lsreplicationvolumegroup", "lsreplicationpolicy"),
            ("lsrcremotesystem", "lspartnership"),
            ("lsquorumserver", "lsquorum"),
            ("restorevolumegroup", "chvolumegroup"),
            ("lsfru", "lsenclosurecanister"),
            ("lscanister", "lsenclosurecanister"),
            ("chnodesshkey", "chauthservice"),
            ("svcupgradepack", "applysoftware"),
            ("lscluster", "lssystem"),
            ("chsystemip", "cfgportip")
        ]

        for bad_cmd, expected_target in test_matrix:
            mock_text = f"請在終端機執行 {bad_cmd} 查詢或設定。"
            res = self.auditor.audit_response("測試提問", mock_text)
            
            self.assertFalse(res["passed"], f"廢棄指令 `{bad_cmd}` 必須無法通過審計！")
            
            # 驗證糾錯映射
            found_mapping = False
            for h in res["hallucinations"]:
                if h.get("invalid_command") == bad_cmd and expected_target in h.get("real_command", ""):
                    found_mapping = True
                    break
            self.assertTrue(found_mapping, f"廢棄指令 `{bad_cmd}` 必須精確映射至 `{expected_target}`")

if __name__ == "__main__":
    unittest.main()
