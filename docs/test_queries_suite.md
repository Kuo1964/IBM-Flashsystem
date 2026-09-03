# IBM FlashSystem 專家系統 - 完整驗證測試題庫 (Test Queries Suite)

本文件彙整了本專案在排查、架構升級、代碼穿透檢索與多輪對話測試過程中所使用的所有真實提問。可用於後續自動化回歸測試、Web Portal 驗證與模型品質評估。

---

## 📑 目錄
1. [一、 錯誤代碼與故障診斷測試題 (Error Codes & Troubleshooting)](#一-錯誤代碼與故障診斷測試題-error-codes--troubleshooting)
2. [二、 產品比較與硬體規格諮詢 (Specs & Comparisons)](#二-產品比較與硬體規格諮詢-specs--comparisons)
3. [三、 CLI 運維指令與特定操作 (Operational CLI Tasks)](#三-cli-運維指令與特定操作-operational-cli-tasks)
4. [四、 大型架構設計、雙站點 HA 與遷移 (Architecture & Migration)](#四-大型架構設計雙站點-ha-與遷移-architecture--migration)
5. [五、 多輪對話追問與邊界防禦測試 (Multi-Turn & Boundary Cases)](#五-多輪對話追問與邊界防禦測試-multi-turn--boundary-cases)

---

## 一、 錯誤代碼與故障診斷測試題 (Error Codes & Troubleshooting)

| 編號 | 測試提問語句 | 預期命中目標 / 官方對照 | 測試目的 |
| :--- | :--- | :--- | :--- |
| **ERR-01** | `我的flashsystem 7200報了一個1059的錯誤該怎麼處理` | `070842 \| Fibre Channel IO port mapping failed. \| 1059` | 驗證 4 位數錯誤碼穿透，不受 FS7200 機型詞稀釋 |
| **ERR-02** | `我的flashsystem 9600報了一個2560的錯誤該怎麼處理` | `010126 \| The usage rate for a flash drive is high... \| 2560` | 驗證快閃磁碟耐損度預警碼穿透與排查步驟 |
| **ERR-03** | `error 1033` | `072522 \| The system board processor has failed. \| 1033` | 驗證極簡短句 4 位數代碼秒級精確召回 |
| **ERR-04** | `FlashSystem 出現 CMMVC1035E 錯誤該如何排除？` | `Volume Protection 磁碟保護機制排查與處置` | 驗證 CMMVC 結構化代碼 Multi-Hop 鏈式檢索 |
| **ERR-05** | `CMMVC1026E 錯誤排查` | `Storage Partition & Ownership Group 隔離處置` | 驗證多租戶分區限制代碼官方手冊直通 |
| **ERR-06** | `CMMVC6368E 錯誤處置` | `Remote Copy & Partnership 鏈路排查` | 驗證遠端複製通訊故障碼處置流程 |

---

## 二、 產品比較與硬體規格諮詢 (Specs & Comparisons)

| 編號 | 測試提問語句 | 關鍵核心評估點 | 測試目的 |
| :--- | :--- | :--- | :--- |
| **SPEC-01** | `幫我比較一下一下這兩個產品的差別FCM5 , FCM4` | FCM4 (AI 勒索軟體檢測) vs FCM5 (磁碟機內硬體去重 In-Drive Deduplication) | 驗證縮寫轉譯精確度、專有名詞保護與無重複標題 |
| **SPEC-02** | `FlashSystem 5200 與 7200 的規格比較` | 控制器架構 (1U 雙橫向 vs 2U 雙垂直堆疊)、PCIe 槽位與電源 | 驗證機型號碼（5200/7200）不被誤判為錯誤代碼 |
| **SPEC-03** | `FlashSystem 5600 規格` | 規格矩陣、快顯緩存容量、支援磁碟協定 | 驗證單一機型標準規格圖表生成 |
| **SPEC-04** | `FlashSystem 9500 PCIe 插槽與擴充規範` | 4U 機箱雙機匣、4 組 PCIe 插槽配置原則、SAS 介面卡料號 `01YM338` | 驗證硬體後視圖與 PCIe 介面卡原廠真理錨定 |

---

## 三、 CLI 運維指令與特定操作 (Operational CLI Tasks)

| 編號 | 測試提問語句 | 預期官方核心指令 | 測試目的 |
| :--- | :--- | :--- | :--- |
| **CLI-01** | `如何修改 node 的 service ip` | `satask chserviceip` / `sainfo lsservicestatus` | 驗證 Tier 1 CLI 極速直答與參數區塊完整性 |
| **CLI-02** | `satask chserviceip 參數語法與注意事項` | `satask chserviceip -serviceip <ip> -gw <gw> -mask <mask> <node_id>` | 驗證維護模式指令安全規範與參數解析 |
| **CLI-03** | `如何使用 lseventlog 查詢未解決的硬體警告事件？` | `lseventlog -expired no -message no` | 驗證事件日誌唯一官方標準指令（嚴禁 lserrorlog） |

---

## 四、 大型架構設計、雙站點 HA 與遷移 (Architecture & Migration)

| 編號 | 測試提問語句 | 涵蓋章節與核心技術 | 測試目的 |
| :--- | :--- | :--- | :--- |
| **ARCH-01** | `請給我一個PBHA IP Quorum設定的建議如果我的兩個FS5600系統放在兩個不同的site IP Quorum該怎麼設計` | 雙站點架構拓撲、第三站點 IP Quorum 應用、`mkipquorum`、網路延遲 < 80ms | 驗證 Tier 4 大型架構設計與極速首發分段生成 |
| **ARCH-02** | `在 FS5200 系統內部，如何使用 NDVM 技術遷移磁區` | `migratevdisk` / `addvdiskcopy` / `splitvdiskcopy` | 驗證無中斷磁區遷移 (Non-Disruptive Volume Migration) |
| **ARCH-03** | `GMCV 轉 PBR 全套實施指南` | 從 Global Mirror Change Volumes 遷移至 Policy-Based Replication | 驗證功能生命週期演進、現代指令 `mkreplicationpolicy` |
| **ARCH-04** | `FlashSystem Grid 儲存網格建置與憑證互信要求` | Coordinator/Member 角色、TLS 互信 `mktruststore`、Single I/O Group 限制 | 驗證 9.1.0+ FlashSystem Grid 最新原廠技術真理 |
| **ARCH-05** | `DRAID 1 與 DRAID 6 的最佳實踐評估` | Distributed RAID 重建速率、磁碟數量下限與空間利用率 | 驗證陣列架構決策評估與原廠最佳實踐 |

---

## 五、 多輪對話追問與邊界防禦測試 (Multi-Turn & Boundary Cases)

| 輪次 | 測試提問語句 | 測試機制與防護重點 |
| :--- | :--- | :--- |
| **第 1 輪** | `我的flashsystem 9600報了一個2560的錯誤該怎麼處理` | 觸發故障診斷流（tier3_troubleshoot），建立對話 Context。 |
| **第 2 輪 (追問)** | `幫我比較一下一下這兩個產品的差別FCM5 , FCM4` | **跨話題突變測試**：驗證系統能保留 FCM5/FCM4 獨立實體，不被上一輪錯誤碼歷史污染。 |
| **第 3 輪 (代名詞)** | `它的重複資料刪除功能在當前版本有什麼限制？` | **代名詞消解測試**：驗證系統能正確識別「它」指向 FCM5，並指出 scan-only 模式。 |
