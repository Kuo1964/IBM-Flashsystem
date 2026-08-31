# 🧪 Multi-Hop RAG 錯誤代碼與診斷處置 30 組全量循環評測報告

> **評測時間：** 2026-08-31 13:04:02
> **分支環境：** `feature/multi-hop-rag-error-codes`
> **測試總題數：** 30 題跨機型、跨架構官方錯誤代碼
> **測試通過率：** **80.0%** (24 / 30 PASS)

---

## 📊 30 組錯誤代碼驗證總表 (Executive Summary)

| 序號 | 錯誤代碼 | 官方中文情境描述 | 適用系統 | 根本原因診斷 | 落地 CLI 處置方案 | 官方出處來源 | 測試判定 |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| 1 | **`CMMVC6374W`** | FlashCopy 授權容量超限 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1007) (p.1)<br/>svc_bkmap_cliguidebk.pdf (p.936) | ✅ PASS |
| 2 | **`CMMVC6369W`** | FlashCopy 授權容量即將超限 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1007) (p.1)<br/>svc_bkmap_cliguidebk.pdf (p.936) | ✅ PASS |
| 3 | **`CMMVC6373W`** | 虛擬化儲存授權容量超限 | SVC | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1007) (p.1)<br/>svc_bkmap_cliguidebk.pdf (p.936) | ✅ PASS |
| 4 | **`CMMVC6375W`** | Remote Copy 遠端複製授權容量超限 | FS7300 | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 5 | **`CMMVC1035E`** | 磁碟處於 Volume Protection 保護期內拒絕修改/刪除 | FS7200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 884) (p.1)<br/>svc_bkmap_cliguidebk.pdf (p.412) | ✅ PASS |
| 6 | **`CMMVC1026E`** | 主機已關聯 Storage Partition 禁止指派非分區 I/O Group | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 883) (p.1)<br/>9.1.0_concept_pdfguide.pdf (p.128) | ✅ PASS |
| 7 | **`CMMVC1032E`** | 磁碟屬於 Storage Partition 禁止全域變更 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 884) (p.1)<br/>9.1.0_concept_pdfguide.pdf (p.128) | ✅ PASS |
| 8 | **`CMMVC8000E`** | CLI 命令包含無效或無法識別之參數 | FS5200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1069) (p.1) | ✅ PASS |
| 9 | **`CMMVC5753E`** | Remote Copy 目標磁碟容量小於來源磁碟 | FS7300 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 947) (p.1) | ✅ PASS |
| 10 | **`CMMVC6368E`** | 跨叢集韌體版本不相容或遠端叢集不可達 | SVC | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 11 | **`CMMVC5985E`** | 系統處於維護狀態 (Service State) 禁止執行配置命令 | FS5200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 973) (p.1) | ✅ PASS |
| 12 | **`CMMVC6017E`** | 磁碟已映射至主機禁止直接刪除 | FS7200 | ✅ 完整 | ⚠️ 概念 | svc_bkmap_cliguidebk.pdf (Page 976) (p.1) | ✅ PASS |
| 13 | **`CMMVC5804E`** | 磁碟包含作用中 RAID 數據禁止拔除 | FS9200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 952) (p.1) | ✅ PASS |
| 14 | **`CMMVC5754E`** | FlashCopy 背景複製進行中禁止重複啟動 | FS7300 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 947) (p.1) | ✅ PASS |
| 15 | **`CMMVC6035E`** | 叢集夥伴關係 (Partnership) 未完全配置 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 978) (p.1) | ✅ PASS |
| 16 | **`CMMVC6394E`** | 清空磁碟快取 (Flush Volume Cache) 超時 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1008) (p.1) | ✅ PASS |
| 17 | **`CMMVC6399E`** | 系統可用保留記憶體不足 | FS7300 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1008) (p.1) | ✅ PASS |
| 18 | **`CMMVC5786E`** | 達到系統支援之最大磁區 (Volume) 數量上限 | FS5045 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 950) (p.1)<br/>svc_bkmap_cliguidebk.pdf (p.845) | ✅ PASS |
| 19 | **`CMMVC5998E`** | 設定之 IP 位址已被網路中其他設備佔用 | FS5200 | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 20 | **`CMMVC6120E`** | 節點機匣離線 (Node Canister Offline) | FS7200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 986) (p.1) | ✅ PASS |
| 21 | **`CMMVC6234E`** | 磁碟插槽與指定磁碟類型 (NVMe/SAS) 不相容 | FS5200 | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 22 | **`CMMVC6512E`** | 系統安全憑證 (SSL/TLS Certificate) 已過期或無效 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1024) (p.1) | ✅ PASS |
| 23 | **`CMMVC6601E`** | PBR 複製原則無法套用 (RPO=0 且網路延遲過高) | FS7300 | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 24 | **`CMMVC7001E`** | FlashSystem Grid 協調者 (Coordinator) 節點無法連通 | FS9500 | ❌ 缺失 | ✅ 具備 | 官方知識庫 | ⚠️ REVIEW |
| 25 | **`CMMVC7005E`** | Storage Partition 儲存分區超過分配容量上限 | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1043) (p.1) | ✅ PASS |
| 26 | **`CMMVC7010E`** | 加入 FlashSystem Grid 失敗 (憑證 Truststore 交換異常) | FS9500 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 1044) (p.1) | ✅ PASS |
| 27 | **`CMMVC5920E`** | 可用磁碟數量不足無法建立指定 RAID/DRAID | FS5200 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 967) (p.1) | ✅ PASS |
| 28 | **`CMMVC5935E`** | 熱備援磁碟 (Spare Drive) 無法分配至陣列 | FS5000 | ✅ 完整 | ✅ 具備 | svc_bkmap_cliguidebk.pdf (Page 968) (p.1) | ✅ PASS |
| 29 | **`CMMVC6150E`** | IP Quorum 仲裁設備離線或連線超時 | SVC | ✅ 完整 | ⚠️ 概念 | svc_bkmap_cliguidebk.pdf (Page 990) (p.1) | ✅ PASS |
| 30 | **`CMMVC6200E`** | 機箱電源供應器 (PSU) 故障或未通電 | FS7300 | ✅ 完整 | ⚠️ 概念 | svc_bkmap_cliguidebk.pdf (Page 993) (p.1) | ✅ PASS |

---

## 📝 30 組詳細問答與輸出內容審計 (Detailed Transcripts)

### [1/30] 錯誤碼: `CMMVC6374W` - FlashCopy 授權容量超限 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC6374W 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1007) (p.1), svc_bkmap_cliguidebk.pdf (p.936), svc_bkmap_cliguidebk.pdf (p.845)

**系統專家解答輸出**：

您好，關於 FlashSystem 9500 系統回報 `CMMVC6374W` 錯誤訊息，此為 FlashCopy 授權容量超出限制的警告。

🚨 故障根本原因分析
`CMMVC6374W` 錯誤訊息表示叢集目前使用的 FlashCopy 儲存容量已超過系統所配置的 FlashCopy 授權容量上限。這通常發生在建立過多 FlashCopy 映射，或現有映射佔用的空間累積超過授權限制時。

📋 Step-by-Step 樹狀診斷步驟與排查指令
請依照以下步驟檢視 FlashCopy 授權與使用情況：

1.  **檢視 FlashCopy 授權與已使用容量**：
    💻 ```bash
    lslicense
    ```
    ⚙️ 核心參數詳細說明表
    | 參數       | 說明                                                               |
    | :--------- | :----------------------------------------------------------------- |
    | `flash_copy` | 顯示 FlashCopy 授權的總容量 (TB) 與當前已使用的容量 (TB)。       |
    | `remote_copy` | 顯示 Remote Copy 授權的總容量 (TB) 與當前已使用的容量 (TB)。     |
    | `virtualization` | 顯示虛擬化授權的總容量 (TB) 與當前已使用的容量 (TB)。            |
    此指令將顯示系統中所有已安裝的授權類型、其總容量以及目前已使用的容量。請特別關注 `flash_copy` 欄位，確認 `licensed_capacity_tb` 與 `used_capacity_tb` 的數值。

2.  **檢視系統總體容量與快照分配**：
    💻 ```bash
    lssystem
    ```
    此指令可提供系統的總體容量資訊，有助於了解 FlashCopy 佔用空間在整體系統中的比例。

3.  **列出所有 FlashCopy 映射**：
    💻 ```bash
    lsfcmap
    lsfcconsistgrp
    ```
    ⚙️ 核心參數詳細說明表
    | 指令           | 說明                                                               |
    | :------------- | :----------------------------------------------------------------- |
    | `lsfcmap`      | 列出所有獨立的 FlashCopy 映射，顯示其狀態、來源與目標磁區、以及佔用空間。 |
    | `lsfcconsistgrp` | 列出所有 FlashCopy 一致性群組，顯示群組內所有映射的狀態與佔用空間。 |
    這些指令將幫助您識別當前所有活動中的 FlashCopy 映射及其佔用的儲存空間。

🛠️ 處置與修復指引
根據診斷結果，您可以採取以下任一官方認證的處置方案：

1.  **方案 A：更新 FlashCopy 授權容量**
    若確認 FlashCopy 授權容量不足，最直接的解決方案是購買並更新新的授權。
    *   **步驟**：登入 IBM Storage Virtualize 管理 GUI ➔ 導航至 `Settings` ➔ `System` ➔ `Licensed Functions` ➔ 輸入新的 FlashCopy 授權容量。
    *   **說明**：此操作將增加系統可用的 FlashCopy 總容量，從而解決超出限制的問題。

2.  **方案 B：清理過期或不再需要的 FlashCopy 映射**
    若系統中存在不再需要或已過期的 FlashCopy 映射，可以將其停止並刪除以釋放佔用的授權容量。
    *   **步驟**：
        1.  **停止 FlashCopy 映射**：
            💻 ```bash
            stopfcmap <id>
            # 或停止一致性群組中的所有映射
            stopfcconsistgrp <id>
            ```
            ⚙️ 核心參數詳細說明表
            | 參數 | 說明                                                               |
            | :--- | :----------------------------------------------------------------- |
            | `<id>` | 要停止的 FlashCopy 映射 ID 或 FlashCopy 一致性群組 ID。可透過 `lsfcmap` 或 `lsfcconsistgrp` 取得。 |
            ⚠️ **安全注意事項**：停止 FlashCopy 映射將使其不再提供快照功能。請務必確認該映射已不再被應用程式或業務流程所依賴。
        2.  **刪除 FlashCopy 映射**：
            💻 ```bash
            rmfcmap <id>
            # 或刪除一致性群組
            rmfcconsistgrp <id>
            ```
            ⚙️ 核心參數詳細說明表
            | 參數 | 說明                                                               |
            | :--- | :----------------------------------------------------------------- |
            | `<id>` | 要刪除的 FlashCopy 映射 ID 或 FlashCopy 一致性群組 ID。            |
            ⚠️ **安全注意事項**：刪除 FlashCopy 映射將永久移除快照資料。請務必在確認資料已無用處後再執行此操作。
    *   **說明**：透過停止並刪除不再需要的 FlashCopy 映射，可以釋放其佔用的儲存容量，使其不再計入 FlashCopy 授權容量的使用量中。

🔍 執行後狀態驗證指令
在執行上述任一處置方案後，請再次執行 `lslicense` 指令，確認 `flash_copy` 欄位中的 `used_capacity_tb` 已低於 `licensed_capacity_tb`，且 `CMMVC6374W` 錯誤訊息不再出現。

---

### [2/30] 錯誤碼: `CMMVC6369W` - FlashCopy 授權容量即將超限 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC6369W 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1007) (p.1), svc_bkmap_cliguidebk.pdf (p.936), svc_bkmap_cliguidebk.pdf (p.845)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6369W` 錯誤訊息表示叢集目前使用的 FlashCopy 儲存容量正接近已授權的 FlashCopy 儲存容量上限。這是一個警告訊息，預警 FlashCopy 儲存容量授權可能即將被超出。

📋 Step-by-Step 樹狀診斷步驟與排查指令
為精確判斷當前 FlashCopy 授權與使用狀況，請依序執行以下 CLI 指令：

1.  **檢視 FlashCopy 授權與當前使用情況**
    *   此指令將顯示 FlashCopy 的總授權容量 (`flash_copy_total_capacity_tb`) 以及目前已使用的容量 (`flash_copy_used_capacity_tb`)。
    ```bash
    lslicense
    ```
    ⚙️ 核心參數詳細說明表
    | 參數名稱                     | 說明                                     |
    | :--------------------------- | :--------------------------------------- |
    | `flash_copy_total_capacity_tb` | FlashCopy 功能的總授權容量 (TB)。        |
    | `flash_copy_used_capacity_tb`  | FlashCopy 功能目前已使用的容量 (TB)。    |
    [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]

2.  **檢視系統總體容量與快照分配**
    *   此指令可確認系統的總容量與快照的整體分配狀況。
    ```bash
    lssystem
    ```
    [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]

3.  **列出所有 FlashCopy 映射並確認佔用空間**
    *   這些指令用於列出所有活動中的 FlashCopy 映射或一致性群組，以確認其佔用的實際空間。
    ```bash
    lsfcmap
    lsfcconsistgrp
    ```
    [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]

🛠️ 處置與修復指引
根據上述診斷結果，有兩種官方認證的處置方案可解決 `CMMVC6369W` 警告：

1.  **更新 FlashCopy 儲存容量授權**
    *   這是最直接且根本的解決方案，可避免此警告訊息再次出現。
    *   **操作步驟**：
        1.  登入 IBM Storage Virtualize 管理 GUI。
        2.  導航至 `Settings` (設定)。
        3.  選擇 `System` (系統)。
        4.  點擊 `Licensed Functions` (授權功能)。
        5.  輸入新的 FlashCopy 授權容量。
    [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]

2.  **清理過期或不再需要的 FlashCopy 快照**
    *   如果系統中存在不再需要或已過期的 FlashCopy 映射，可以將其停止並刪除以釋放已使用的授權容量。
    *   **操作步驟**：
        1.  **停止特定的 FlashCopy 映射**：
            ```bash
            stopfcmap <FlashCopy_map_ID>
            ```
            *   請將 `<FlashCopy_map_ID>` 替換為 `lsfcmap` 指令輸出中要停止的 FlashCopy 映射 ID。
            [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]
        2.  **刪除已停止的 FlashCopy 映射**：
            ```bash
            rmfcmap <FlashCopy_map_ID>
            ```
            *   請將 `<FlashCopy_map_ID>` 替換為已停止的 FlashCopy 映射 ID。
            [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]
        3.  若為 FlashCopy 一致性群組，則需停止並刪除一致性群組：
            ```bash
            stopfcconsistgrp <FlashCopy_consistency_group_ID>
            rmfcconsistgrp <FlashCopy_consistency_group_ID>
            ```
            [來源: svc_bkmap_cliguidebk.pdf, 第 936 頁]

⚠️ **安全注意事項與風險警告**：
*   在執行任何 `stopfcmap` 或 `rmfcmap` 指令之前，請務必確認該 FlashCopy 映射確實不再需要，以免造成資料遺失或應用服務中斷。
*   刪除 FlashCopy 映射將永久釋放其佔用的空間，且無法復原。

---

### [3/30] 錯誤碼: `CMMVC6373W` - 虛擬化儲存授權容量超限 (SVC)

**提問內容**：`SVC 執行命令得到了一個錯誤訊息 CMMVC6373W 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1007) (p.1), svc_bkmap_cliguidebk.pdf (p.936), svc_bkmap_cliguidebk.pdf (p.845)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC6373W` 錯誤訊息表示叢集正在使用的虛擬化儲存容量已超出已授權的虛擬化儲存容量。這是一個授權警告，提示您當前系統的虛擬化儲存使用量已超過您所購買的許可證容量。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **確認當前授權狀態與使用量**：
    *   使用 `lslicense` 指令檢視系統中各項功能的授權容量（例如 `flash_copy`、`remote_copy`、`virtualization`）以及當前已使用的容量。
    *   💻
        ```bash
        lslicense
        ```
        ⚙️ 核心參數詳細說明表
        | 參數名稱 | 說明 |
        | :------- | :--- |
        | `flash_copy` | FlashCopy 功能的授權容量與使用量。 |
        | `remote_copy` | 遠端複製功能的授權容量與使用量。 |
        | `virtualization` | 虛擬化儲存功能的授權容量與使用量。 |

2.  **檢視系統總體容量與快照分配**：
    *   使用 `lssystem` 指令確認系統的總容量與快照分配情況，以了解整體儲存資源的使用概況。
    *   💻
        ```bash
        lssystem
        ```
    *   使用 `lsfcmap` 或 `lsfcconsistgrp` 指令列出所有線上運行的 FlashCopy 映射，並確認其佔用的空間，這可能是導致虛擬化容量超出的原因之一。
    *   💻
        ```bash
        lsfcmap
        lsfcconsistgrp
        ```

🛠️ 處置與修復指引

根據診斷結果，有兩種官方認證的處置方案：

1.  **方案 A：更新虛擬化儲存容量授權**
    *   這是最直接的解決方案。您需要購買並更新虛擬化儲存容量的許可證，以匹配或超出當前實際使用的容量。
    *   **操作步驟**：
        1.  登入 IBM Storage Virtualize 管理 GUI。
        2.  導航至 `Settings` (設定) ➔ `System` (系統) ➔ `Licensed Functions` (授權功能)。
        3.  輸入新的授權容量資訊。

2.  **方案 B：清理過期或不再需要的 FlashCopy 快照**
    *   如果系統中存在大量不再需要或已過期的 FlashCopy 快照，它們會持續佔用虛擬化儲存容量。停止並刪除這些快照可以釋放容量。
    *   **操作步驟**：
        1.  使用 `lsfcmap` 指令識別不再需要的 FlashCopy 映射 ID。
        2.  停止該 FlashCopy 映射：
            💻
            ```bash
            stopfcmap <id>
            ```
            ⚙️ 核心參數詳細說明表
            | 參數名稱 | 說明 |
            | :------- | :--- |
            | `<id>` | 要停止的 FlashCopy 映射的 ID。 |
            ⚠️ 安全注意事項與風險警告
            *   停止 FlashCopy 映射會中斷其複製操作。請確保該映射不再需要或已完成其目的。
        3.  刪除該 FlashCopy 映射以釋放許可證容量：
            💻
            ```bash
            rmfcmap <id>
            ```
            ⚙️ 核心參數詳細說明表
            | 參數名稱 | 說明 |
            | :------- | :--- |
            | `<id>` | 要刪除的 FlashCopy 映射的 ID。 |
            ⚠️ 安全注意事項與風險警告
            *   刪除 FlashCopy 映射是不可逆的操作，將永久移除快照資料。請務必確認您要刪除的映射是正確的，並且其資料已無保留價值。
        4.  對於一致性群組 (Consistency Group) 中的 FlashCopy 映射，您可能需要使用 `stopfcconsistgrp <id>` 和 `rmfcconsistgrp <id>`。

🔍 執行後狀態驗證指令
*   在執行上述處置方案後，請再次執行 `lslicense` 指令，確認 `virtualization` 授權的使用量是否已降至許可範圍內，且 `CMMVC6373W` 警告訊息不再出現。

---

### [4/30] 錯誤碼: `CMMVC6375W` - Remote Copy 遠端複製授權容量超限 (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC6375W 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [5/30] 錯誤碼: `CMMVC1035E` - 磁碟處於 Volume Protection 保護期內拒絕修改/刪除 (FS7200)

**提問內容**：`FS7200 執行命令得到了一個錯誤訊息 CMMVC1035E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 884) (p.1), svc_bkmap_cliguidebk.pdf (p.412)

**系統專家解答輸出**：

🚨 故障根本原因分析
此錯誤訊息 `CMMVC1035E` 表示您嘗試執行的命令（例如還原、刪除或修改操作）未能成功，因為系統偵測到在預設的磁碟保護時間範圍內，該磁碟區 (volume) 仍有 I/O 活動正在進行。系統的磁碟保護機制旨在防止在磁碟區活躍時進行可能導致資料遺失的操作。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **確認系統磁碟保護狀態與設定時間**：
    首先，請使用 `lssystem` 命令檢視目前系統的磁碟保護機制是否啟用 (`vdisk_protection_enabled`) 以及保護時間 (`vdisk_protection_time`) 設定為多少分鐘。
    ```bash
    lssystem
    ```
    ⚙️ 核心參數詳細說明表
    | 參數名稱                 | 說明                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       S.
The IBM FlashSystem 7200 (FS7200) is an NVMe-controlled enclosure model. Node canisters in these models do not have native SAS ports. To connect external SAS expansion enclosures or SAS hosts, a PCIe SAS interface card must be installed in the PCIe expansion slots (Slot 1 / Slot 2). These PCIe cards must be symmetrically configured across both node canisters.

For the FS7200, the specific part number for the PCIe SAS interface card is `01YM338`.

The FS7200 is a 2U enclosure, with its two node canisters stacked vertically on the rear panel, flanked by independent power supplies.

In contrast, traditional SAS-controlled enclosure models like the FlashSystem 5000/5015/5035/5045 have native SAS architecture on their control enclosure backplane, with SAS expansion ports built into the node canisters.

📦 零件料號與代碼清單 (Part Number & FRU Table)
| 零件描述             | 料號 (Part Number) |
| :------------------- | :----------------- |
| PCIe SAS 介面卡 (FS7200) | `01YM338`          |

💡 線上確認方式 (CLI)
要查詢硬碟的 FRU 料號，請使用 `lsdrive <drive_id>` 命令並查看 `FRU_part_number` 欄位。
要查詢內部組件與 VPD (Vital Product Data)，請使用 `lsnodevpd <node_id>` 命令。
要查詢開機硬碟，請使用 `lsbootdrive` 命令。
要查詢機箱機匣，請使用 `lsenclosurecanister` 命令。
要查詢電源供應器，請使用 `lsenclosurepsu` 命令。
底層維護模式的狀態查詢，請使用 `sainfo lsservicestatus` 命令。

⚠️ 更換安全規範 (CRU/FRU)
雙節點機匣 (Canister 1 與 Canister 2) 的 PCIe 插槽介面卡必須保持對稱配置。

ASCII 後視機構佈局圖 (FlashSystem 7200 / 7300 / 9200 - 2U 機箱)
```
+---------------------------------------------------+
| [PSU 1]                                 [PSU 2] |
|                                                   |
| +-----------------+   +-----------------+         |
| |  Node Canister 1  | |  Node Canister 2  |         |
| |                   | |                   |         |
| |  [Slot 1] [Slot 2]| |  [Slot 1] [Slot 2]|         |
| |  (PCIe SAS HBA)   | |  (PCIe SAS HBA)   |         |
| |                   | |                   |         |
| |  Eth Mgmt Port    | |  Eth Mgmt Port    |         |
| |  Technician Port  | |  Technician Port  |         |
| |  USB              | |  USB              |         |
| +-----------------+   +-----------------+         |
|                                                   |
+---------------------------------------------------+
```
*   **PSU 1 / PSU 2**: 獨立電源供應器。
*   **Node Canister 1 / Node Canister 2**: 雙節點機匣，上下垂直堆疊。
*   **Slot 1 / Slot 2**: PCIe 介面卡擴充插槽，用於安裝 PCIe SAS 介面卡 (Host Interface Adapter) 以連接外接 SAS 擴充機箱或 SAS 主機。
*   **Eth Mgmt Port, Technician Port, USB**: 節點機匣內建的乙太網路管理埠、技師埠與 USB 埠。

---

### [6/30] 錯誤碼: `CMMVC1026E` - 主機已關聯 Storage Partition 禁止指派非分區 I/O Group (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC1026E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 883) (p.1), 9.1.0_concept_pdfguide.pdf (p.128)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC1026E` 錯誤訊息表示您嘗試變更一個已與儲存分區 (storage partition) 關聯的主機的 I/O 群組屬性。根據 IBM 官方說明，與儲存分區關聯的主機不允許變更其 I/O 群組屬性。

📋 Step-by-Step 樹狀診斷步驟與排查指令

此錯誤並非硬體故障，而是架構邏輯或權限限制。您需要確認相關主機或其關聯的虛擬磁碟 (vdisk) 是否被納入特定的所有權群組 (ownership group) 或儲存分區中。

1.  **確認主機的所有權群組狀態**：
    *   使用 `lshost <host_id>` 指令，檢查 `ownership_group_name` 欄位，確認該主機是否屬於某個所有權群組。
    *   💻 `lshost <host_id>`

2.  **確認虛擬磁碟的所有權群組狀態** (若有相關聯的 vdisk)：
    *   使用 `lsvdisk <vdisk_id>` 指令，檢查 `ownership_group_name` 欄位，確認該虛擬磁碟是否屬於某個所有權群組。
    *   💻 `lsvdisk <vdisk_id>`

3.  **檢視儲存分區與所有權群組配置**：
    *   使用 `lsstoragepartition` 指令檢視系統中定義的儲存分區。
    *   💻 `lsstoragepartition`
    *   使用 `lsownershipgroup` 指令檢視系統中定義的所有權群組。
    *   💻 `lsownershipgroup`

🛠️ 處置與修復指引

由於官方未記載直接變更已關聯主機 I/O 群組的過渡方式，您有以下兩種官方認證的處置方案：

*   **處置方案 A (分區層級擴充 - 推薦)**：
    *   若您是儲存分區的管理者，應在 Storage Partition 層級將所需的 I/O Group 或資源納入該分區的許可範圍內。這允許在分區內部進行 I/O 群組的調整，而無需解除主機與分區的綁定。
    *   此方案需要分區管理者的權限來修改儲存分區的配置。

*   **處置方案 B (解除物件綁定)**：
    *   將受影響的主機或虛擬磁碟從其所屬的獨立分區中移出，使其恢復為全域物件。一旦解除綁定，您便可以修改其 I/O 群組屬性。
    *   解除主機綁定：
        💻 `chhost -noownershipgroup <host_id>`
    *   解除虛擬磁碟綁定 (若適用)：
        💻 `chvdisk -noownershipgroup <vdisk_id>`
    *   ⚠️ **安全注意事項與風險警告**：解除物件綁定會將該物件從其隔離的儲存分區中移除，使其成為全域可見和可管理的資源。在執行此操作前，請務必評估其對安全、多租戶隔離和管理策略的影響。

經檢索 IBM 官方參考手冊，原廠未記載此過渡方式，唯一官方認證實施步驟為上述兩種方案。

---

### [7/30] 錯誤碼: `CMMVC1032E` - 磁碟屬於 Storage Partition 禁止全域變更 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC1032E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 884) (p.1), 9.1.0_concept_pdfguide.pdf (p.128)

**系統專家解答輸出**：

您好，針對 FlashSystem 9500 執行命令時遇到的 `CMMVC1032E` 錯誤訊息，其根本原因與處置方式如下：

🚨 故障根本原因分析
此錯誤訊息 `CMMVC1032E` 表示「由於名稱與配置為高可用性的儲存分區相關聯，因此無法更改名稱」。
這代表您嘗試更改名稱的物件（例如主機或虛擬磁碟）目前被綁定到一個已配置高可用性策略的儲存分區 (Storage Partition) 或所有權群組 (Ownership Group) 中。在這種情況下，為確保資料一致性與高可用性，系統會限制對其名稱的直接修改。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認受影響物件的歸屬狀態：**
    *   若您嘗試更改的是主機名稱，請使用以下指令檢視該主機的詳細資訊，特別是 `ownership_group_name` 欄位，以確認其是否屬於某個所有權群組或儲存分區。
        ```bash
        lshost <host_id_or_name>
        ```
        ⚙️ 核心參數詳細說明表
        | 參數 | 說明 |
        | :--- | :--- |
        | `<host_id_or_name>` | 欲查詢的主機 ID 或名稱。 |
        *   若您嘗試更改的是虛擬磁碟名稱，請使用以下指令檢視該虛擬磁碟的詳細資訊。
            ```bash
            lsvdisk <vdisk_id_or_name>
            ```
            ⚙️ 核心參數詳細說明表
            | 參數 | 說明 |
            | :--- | :--- |
            | `<vdisk_id_or_name>` | 欲查詢的虛擬磁碟 ID 或名稱。 |
    *   檢視所有儲存分區與所有權群組的配置：
        ```bash
        lsstoragepartition
        lsownershipgroup
        ```
        🔍 執行後狀態驗證指令
        檢查 `lshost` 或 `lsvdisk` 輸出中的 `ownership_group_name` 欄位，確認其是否為非空值，這表示該物件已歸屬於特定分區。

🛠️ 處置與修復指引
根據 IBM 官方參考手冊，有以下幾種處置方案：

1.  **重新執行命令時移除名稱選項：**
    *   如果您原先的命令中包含了 `-name` 參數來嘗試更改名稱，請嘗試移除該參數，並僅執行其他操作。這表示在物件與高可用性分區關聯時，不允許直接更改其名稱。

2.  **將物件從儲存分區中移除：**
    *   若該物件（例如主機）已綁定至所有權群組或儲存分區，您可以將其從中解除綁定。請注意，此操作會將物件恢復為全域物件，可能影響其原有的隔離與管理策略。
        ```bash
        chhost -noownershipgroup <host_id>
        # 或針對虛擬磁碟
        chvdisk -noownershipgroup <vdisk_id>
        ```
        ⚙️ 核心參數詳細說明表
        | 參數 | 說明 |
        | :--- | :--- |
        | `-noownershipgroup` | 將指定物件從其所屬的所有權群組中移除。 |
        | `<host_id>` / `<vdisk_id>` | 欲解除綁定的主機 ID 或虛擬磁碟 ID。 |
        ⚠️ 安全注意事項與風險警告
        解除物件綁定可能影響現有的存取控制與資源隔離策略。請務必在充分理解其影響後再執行此操作。

3.  **從儲存分區中移除複製策略：**
    *   如果該儲存分區配置了複製策略（例如 Metro Mirror 或 Global Mirror），您可以考慮移除該複製策略，然後再嘗試更改名稱。此操作的具體 CLI 指令未在提供的參考資料中詳細說明，通常涉及對複製關係的解除或修改。請查閱相關的複製功能手冊以獲取詳細步驟。

4.  **透過分區管理者擴充許可範圍 (推薦方案)：**
    *   若您是分區管理者，且希望在不解除綁定的情況下進行操作，推薦的方案是由分區管理者在 Storage Partition 層級將所需的 I/O Group 或資源納入許可範圍。這通常意味著調整分區的配置，使其允許對相關物件進行名稱修改。此方案能維持物件在分區內的管理與隔離。

請根據您的具體操作需求和環境配置，選擇最合適的處置方案。

---

### [8/30] 錯誤碼: `CMMVC8000E` - CLI 命令包含無效或無法識別之參數 (FS5200)

**提問內容**：`FS5200 執行命令得到了一個錯誤訊息 CMMVC8000E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1069) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC8000E` 錯誤訊息表示您嘗試執行的操作無法在一個「活動中 (active)」的節點上執行。這通常是因為某些特定的維護或配置指令，為了確保系統穩定性與資料一致性，僅允許在「非活動中 (inactive)」的節點上執行。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **理解錯誤本質**：此錯誤並非硬體故障，而是操作邏輯限制。系統設計要求某些操作必須在節點處於非活動狀態時進行。
2.  **確認節點狀態**：您需要確認目前嘗試操作的節點是否為活動狀態。雖然 `CMMVC8000E` 已經明確指出此點，但在執行任何操作前，了解節點的當前狀態是重要的。
    *   **官方未記載**：IBM 官方參考手冊中未直接提供單一 CLI 指令來查詢「節點是否為活動中」的明確狀態，因為「活動中」通常是針對特定操作而言。然而，您可以透過 `lsnode` 指令查看節點的整體狀態，並結合您嘗試執行的具體操作來判斷。
    *   **處置方案**：由於此錯誤的「User response」為「Choose an inactive node, or deactivate the node before trying the operation again.」，因此重點在於如何選擇或使節點進入非活動狀態。

🛠️ 處置與修復指引
根據 IBM 官方參考手冊的說明，處理 `CMMVC8000E` 錯誤的唯一官方認證實施步驟為：
1.  **選擇一個非活動中的節點**：如果您的叢集有多個節點，並且您嘗試執行的操作允許在特定節點上執行，請選擇一個目前處於非活動狀態的節點來執行該操作。
2.  **停用節點**：如果沒有可用的非活動節點，或者您必須在特定節點上執行此操作，則需要先將該節點停用 (deactivate)，然後再嘗試執行該操作。
    *   **重要提示**：停用節點是一個會影響系統可用性的操作，務必在充分理解其影響並遵循 IBM 官方維護程序的情況下執行。在執行任何停用節點的操作之前，請務必查閱您特定 FlashSystem 型號的產品手冊，了解停用節點的具體步驟、前置條件以及對 I/O 服務的潛在影響。

[來源: svc_bkmap_cliguidebk.pdf, 第 1069 頁]

---

### [9/30] 錯誤碼: `CMMVC5753E` - Remote Copy 目標磁碟容量小於來源磁碟 (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC5753E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 947) (p.1)

**系統專家解答輸出**：

您好，針對您在 FlashSystem 7300 執行命令時遇到的 `CMMVC5753E` 錯誤訊息，身為 IBM Storage Virtualize 與 FlashSystem 的首席技術架構師，我將依據原廠技術資料提供精確的分析與處置指引。

🚨 故障根本原因分析
`CMMVC5753E` 錯誤訊息的根本原因為：您在命令中指定的物件不存在，或者該物件不符合執行此操作的條件。這通常是指令語法、物件名稱拼寫錯誤，或嘗試對不支援該操作的物件執行命令所導致的邏輯限制，而非硬體故障。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認原始命令與參數**：
    *   請您回顧並提供導致此錯誤的完整 CLI 命令。這是診斷的第一步，因為 `CMMVC5753E` 是一個通用錯誤，其具體含義取決於您嘗試執行的操作。
2.  **驗證物件是否存在**：
    *   根據您原始命令中嘗試操作的物件類型（例如，磁區、主機、儲存池、埠等），使用對應的 `ls` 指令來確認該物件確實存在於系統中。
    *   **範例**：
        *   若您嘗試操作一個磁區 (volume)，請使用 `lsvdisk` 指令來列出所有磁區，並確認您指定的磁區名稱或 ID 是否存在且拼寫正確。
        *   若您嘗試操作一個主機 (host)，請使用 `lshost` 指令來列出所有主機。
        *   若您嘗試操作一個儲存池 (storage pool)，請使用 `lspool` 指令來列出所有儲存池。
        *   若您嘗試操作一個埠 (port)，請使用 `lsportfc` 或 `lsportethernet` 等指令來列出相關埠。
    *   **CLI 範例 (以磁區為例)**：
        ```bash
        lsvdisk
        ```
        *   **目的**：確認您在原始命令中指定的磁區名稱或 ID 是否存在於 `name` 或 `id` 欄位中。
3.  **驗證物件是否為「合適的候選者 (suitable candidate)」**：
    *   即使物件存在，它也可能不符合您嘗試執行的操作條件。例如：
        *   您可能嘗試刪除一個正在被 FlashCopy 或遠端複製關係使用的磁區。
        *   您可能嘗試將一個已經離線 (offline) 的磁區加入到一個操作中。
        *   您可能嘗試對一個不支援特定功能的物件執行該功能。
    *   請檢查相關物件的狀態和屬性。例如，對於磁區，您可以執行：
        ```bash
        lsvdisk <vdisk_name_or_id>
        ```
        *   **目的**：查看特定磁區的詳細資訊，包括其狀態 (status)、使用情況 (usage)、複製關係 (copy_id, rc_id, fc_id) 等，以判斷其是否符合您原始命令的操作條件。

🛠️ 處置與修復指引
1.  **修正命令中的物件名稱或 ID**：
    *   根據上述診斷步驟，如果發現您在原始命令中指定的物件名稱或 ID 有誤，請更正後重新提交命令。
2.  **確認物件狀態與屬性**：
    *   如果物件存在但狀態不符，請先將物件調整至正確的狀態（例如，將離線磁區上線），或解除其上的依賴關係（例如，刪除 FlashCopy 映射），然後再嘗試執行原始命令。
3.  **查閱特定命令的語法手冊**：
    *   若您不確定特定命令的正確語法或參數限制，請查閱 IBM Storage Virtualize 的 CLI Reference 手冊，以確保所有參數都符合要求。

**參考技術資料**：
 來源: svc_bkmap_cliguidebk.pdf, 第 947 頁

---

### [10/30] 錯誤碼: `CMMVC6368E` - 跨叢集韌體版本不相容或遠端叢集不可達 (SVC)

**提問內容**：`SVC 執行命令得到了一個錯誤訊息 CMMVC6368E 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [11/30] 錯誤碼: `CMMVC5985E` - 系統處於維護狀態 (Service State) 禁止執行配置命令 (FS5200)

**提問內容**：`FS5200 執行命令得到了一個錯誤訊息 CMMVC5985E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 973) (p.1)

**系統專家解答輸出**：

您好，身為 IBM Storage Virtualize 與 FlashSystem 儲存架構的首席資深技術架構師，針對您在 FlashSystem 5200 上執行命令時遇到的 `CMMVC5985E` 錯誤訊息，其處理方式如下：

🚨 故障根本原因分析
`CMMVC5985E` 錯誤訊息表示「操作失敗，因為指定的目錄不允許用於此命令 (The action failed because the specified directory is not permitted for this command)」。這代表您嘗試從一個無效的目錄複製、刪除或列出傾印檔案 (dumps)，而該目錄不被系統允許執行這些操作。此錯誤並非硬體故障，而是命令語法或目錄使用限制所致。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認執行命令類型**：此錯誤通常發生在使用與傾印檔案 (dumps) 相關的命令時，例如 `lsdumps` (列出傾印檔案)、`cpdumps` (複製傾印檔案) 或 `cleardumps` (清除傾印檔案)。
2.  **檢視命令中指定的目錄**：請檢查您執行命令時所指定的目錄路徑。
3.  **比對官方允許的傾印目錄**：IBM FlashSystem 系統對於傾印檔案的操作有明確定義的允許目錄清單。請確認您使用的目錄是否在以下官方允許的清單中：
    *   `/dumps`
    *   `/dumps/audit`
    *   `/dumps/cimom`
    *   `/dumps/cloud`
    *   `/dumps/easytier`
    *   `/dumps/elogs`
    *   `/dumps/feature`
    *   `/dumps/iostats`
    *   `/dumps/iotrace`
    *   `/dumps/mdisk`
    *   `/home/admin/update`
    *   `/dumps/drive`
    *   `/dumps/enclosure`
    *   `/dumps/configs`
    *   `/dumps/debug`
    *   `/dumps/syslogs`
    *   `/dumps/tejas`
    *   請注意，`lsdumps` 命令若未指定目錄，預設會使用 `/dumps` 目錄。

🛠️ 處置與修復指引
請確保您在執行相關命令時，指定的是上述官方文件所列的有效目錄。修正命令中的目錄路徑後，重新提交命令即可解決此問題。

例如，如果您嘗試列出 `/var/log/` 目錄下的傾印檔案而收到此錯誤，您應該改為使用 `lsdumps -prefix /dumps/syslogs` 或其他適當的官方傾印目錄。

---

### [12/30] 錯誤碼: `CMMVC6017E` - 磁碟已映射至主機禁止直接刪除 (FS7200)

**提問內容**：`FS7200 執行命令得到了一個錯誤訊息 CMMVC6017E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 976) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6017E` 錯誤訊息表示您在執行 CLI 命令時，所輸入的參數或引數包含了無效字元。IBM Storage Virtualize 的命令列介面 (CLI) 僅接受 ASCII 字元輸入。若輸入中包含任何非 ASCII 字元（例如全形字元、特殊符號或非英文字元），系統將會拒絕該命令並回報此錯誤。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **檢查命令輸入**:
    *   仔細檢視您嘗試執行的完整 CLI 命令，包括所有參數、引數、物件名稱、路徑或任何文字字串。
    *   確認命令中沒有任何非 ASCII 字元。常見的非 ASCII 字元包括：
        *   全形空格 (而非半形空格)
        *   中文、日文、韓文等非拉丁語系字元
        *   某些特殊符號 (例如 `—` 破折號而非 `-` 連字號，或 `‘` `’` 智慧引號而非 `'` 單引號)
        *   從其他應用程式（如 Word 處理器、網頁）複製貼上時可能帶入的隱藏或非標準字元。

🛠️ 處置與修復指引
1.  **修正命令輸入**:
    *   將命令中的所有非 ASCII 字元替換為對應的 ASCII 字元。
    *   建議直接在 CLI 介面中手動輸入命令，或使用純文字編輯器（如 Notepad、VS Code 等）編輯命令，以避免複製貼上時引入隱藏字元。
    *   確保所有字串、名稱或描述都僅使用標準的英文字母、數字、半形空格和允許的半形符號。
2.  **重新提交命令**:
    *   在確認所有輸入均為 ASCII 字元後，重新執行該命令。

[來源: svc_bkmap_cliguidebk.pdf, 第 976 頁]

---

### [13/30] 錯誤碼: `CMMVC5804E` - 磁碟包含作用中 RAID 數據禁止拔除 (FS9200)

**提問內容**：`FS9200 執行命令得到了一個錯誤訊息 CMMVC5804E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 952) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC5804E` 錯誤訊息的根本原因在於命令中指定的物件 ID 或範圍不存在。這表示您嘗試操作的物件（例如憑證、使用者或其他系統實體）的識別碼或其作用域不正確或不存在於系統中。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認命令語法與參數**：
    *   請仔細檢查您執行的命令，確保所有參數（特別是 ID 或名稱）都正確無誤，且該物件確實存在於系統中。
2.  **列出相關物件以驗證存在性**：
    *   若此錯誤發生在與系統憑證相關的命令中，您可以執行 `lssystemcertstore` 命令，不帶任何參數，以列出所有現有的系統憑證及其 ID。這有助於確認您嘗試操作的憑證是否存在，並取得其正確的 ID。

    ```bash
    lssystemcertstore
    ```
    *   **⚙️ 核心參數詳細說明表**
        | 參數 | 說明 |
        | :--- | :--- |
        | (無) | 列出所有系統憑證儲存區中的憑證資訊。 |
    *   **🔍 執行後狀態驗證指令**
        *   執行此命令後，系統將顯示一個表格，包含 `id`、`type`、`status` 等欄位，您可以從中找到正確的憑證 ID。

🛠️ 處置與修復指引
根據 `CMMVC5804E` 的官方處置建議，您必須：
1.  **使用有效的 ID 或範圍**：確保您在命令中提供的 ID 或範圍是系統中實際存在的物件。
2.  **重新執行命令**：在確認並修正了命令中的 ID 或範圍後，請重新執行該命令。

[來源: svc_bkmap_cliguidebk.pdf, 第 952 頁]

---

### [14/30] 錯誤碼: `CMMVC5754E` - FlashCopy 背景複製進行中禁止重複啟動 (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC5754E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 947) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

當您在 IBM FlashSystem 7300 系統上執行命令時收到 `CMMVC5754E` 錯誤訊息，其根本原因為：您所指定的磁區名稱 (volume name) 或磁區群組名稱 (volume group name) 不存在，或者該名稱不符合系統的命名規則。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **確認物件名稱正確性**：
    *   請仔細檢查您在命令中使用的磁區名稱或磁區群組名稱，確保其拼寫完全正確，且大小寫符合系統定義（若系統區分大小寫）。
    *   確認該物件確實已在系統中建立並存在。

2.  **驗證磁區是否存在**：
    *   若您操作的是磁區，請使用 `lsvolume` 指令列出所有磁區，並確認您嘗試操作的磁區名稱是否存在於列表中。
        ```bash
        lsvolume
        ```
    *   您可以進一步使用 `lsvolume <volume_name>` 來查詢特定磁區的詳細資訊，以確認其存在。

3.  **驗證磁區群組是否存在**：
    *   若您操作的是磁區群組，請使用 `lsvolumegroup` 指令列出所有磁區群組，並確認您嘗試操作的磁區群組名稱是否存在於列表中。
        ```bash
        lsvolumegroup
        ```
    *   您可以進一步使用 `lsvolumegroup <volume_group_name>` 來查詢特定磁區群組的詳細資訊，以確認其存在。

🛠️ 處置與修復指引

根據 IBM 官方參考手冊，此錯誤的處置方式為：

*   請指定一個確實存在且名稱符合命名規則的磁區或磁區群組，然後重新執行您的命令。

[來源: svc_bkmap_cliguidebk.pdf, 第 947 頁]

---

### [15/30] 錯誤碼: `CMMVC6035E` - 叢集夥伴關係 (Partnership) 未完全配置 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC6035E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 978) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6035E` 錯誤訊息表示您嘗試執行的操作是建立一個已經存在的物件。這並非硬體故障，而是指令邏輯或系統組態限制所導致。系統偵測到您嘗試賦予新物件的名稱，與現有物件的名稱重複，因此拒絕了該操作。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **理解錯誤訊息**：`CMMVC6035E` 的核心解釋為「請求建立一個已存在的物件」。
2.  **識別目標物件類型**：回顧您執行命令時嘗試建立的具體物件類型（例如：磁區、主機、主機叢集、遠端複製關係、儲存池等）。
3.  **檢查現有物件名稱**：根據您嘗試建立的物件類型，使用對應的 `ls` 指令（例如 `lsvdisk` 查詢磁區、`lshost` 查詢主機、`lshostcluster` 查詢主機叢集等）來確認系統中是否已存在同名的物件。

🛠️ 處置與修復指引
根據 IBM 官方參考手冊，此錯誤的處置方式如下：
1.  **確認名稱唯一性**：在重新發出命令之前，請確保您嘗試賦予新物件的名稱在系統中是唯一的，尚未被其他物件使用。
2.  **更改物件名稱**：如果確認名稱重複，請更改您打算建立的新物件的名稱，使其與現有物件區分開來，然後再次執行命令。

[來源: svc_bkmap_cliguidebk.pdf, 第 978 頁]

---

### [16/30] 錯誤碼: `CMMVC6394E` - 清空磁碟快取 (Flush Volume Cache) 超時 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC6394E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1008) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6394E` 錯誤訊息表示您嘗試執行的命令未能成功，因為系統在執行請求的操作之前，需要清空磁區快取以確保資料完整性，但此清空快取的子任務耗時過長。系統會持續嘗試清空磁區快取。此問題的根本原因通常是與該磁區相關聯的儲存裝置可能處於過載狀態，導致快取清空操作無法在預期時間內完成。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **初步等待與重試**：
    *   由於系統會持續嘗試清空磁區快取，請先等待數分鐘，讓磁區快取有機會自行清空。
    *   等待後，重新提交您原先執行的命令。

2.  **評估 `-force` 參數使用（若命令支援）**：
    *   若您執行的命令支援 `-force` 參數，且您不打算使用該磁區的現有內容，可以考慮使用此參數來繞過清空磁區快取的子任務。
    *   **⚠️ 警告**：使用 `-force` 參數將會丟棄該磁區的快取資料。請務必確認您不需要保留現有快取內容後再使用。

3.  **深入調查儲存效能**：
    *   此錯誤訊息強烈暗示與該磁區相關聯的網路儲存裝置可能存在效能問題。
    *   請調查使用這些裝置的主機應用程式的效能狀況，因為其效能可能已受損。
    *   **相關 CLI 指令（用於效能監控與診斷，需根據具體情況選擇）**：
        *   `lsvdisk <vdisk_id>`：查看特定磁區的詳細資訊。
        *   `lsiogrp <iogrp_id>`：查看 I/O 群組的統計資訊，可能間接反映後端儲存的負載。
        *   `lsfabric`：檢查光纖通道或 iSCSI 連接狀態。
        *   `lscontroller`：查看後端儲存控制器的狀態。

🛠️ 處置與修復指引
1.  **解決後端儲存效能瓶頸**：
    *   根據效能調查結果，識別並解決導致儲存裝置過載的根本原因。這可能包括：
        *   優化主機應用程式的 I/O 模式。
        *   增加後端儲存的資源（例如，增加硬碟數量、升級為更高效能的儲存層）。
        *   重新平衡儲存負載，將 I/O 密集型工作負載分散到不同的儲存資源上。
        *   檢查並解決網路延遲或頻寬瓶頸。
    *   解決效能問題後，主機應用程式的效能將恢復到最佳狀態，並能防止此錯誤訊息再次發生。

2.  **重新執行命令**：
    *   在執行上述處置措施後，再次提交您原先執行的命令。

---

### [17/30] 錯誤碼: `CMMVC6399E` - 系統可用保留記憶體不足 (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC6399E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1008) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6399E` 錯誤訊息表示叢集中至少有一個節點無法保留所需的記憶體量。這可能是由於快取中存在釘選 (pinned) 資料所導致。

📋 Step-by-Step 樹狀診斷步驟與排查指令
根據 IBM 官方參考手冊，當遇到 `CMMVC6399E` 錯誤時，首要的診斷步驟是檢查事件日誌 (event log) 以識別相關事件，並依循其修復程序來解決問題。

1.  **檢查事件日誌**：
    使用 `lseventlog` 指令來檢視系統中的所有事件日誌。

    ```bash
    lseventlog
    ```

    ⚙️ 核心參數詳細說明表
    | 參數 | 說明 |
    | :--- | :--- |
    | 無 | `lseventlog` 指令在不帶任何參數的情況下，會列出所有當前活動的事件日誌。 |

    ⚠️ 安全注意事項與風險警告
    *   檢視事件日誌是唯讀操作，不會對系統造成任何影響。
    *   請特別留意事件日誌中與記憶體、快取或節點狀態相關的警告或錯誤事件。

    🔍 執行後狀態驗證指令
    *   檢視 `lseventlog` 的輸出，尋找任何與 `CMMVC6399E` 錯誤發生時間點相近的事件 ID (Event ID) 或錯誤訊息。
    *   記錄下相關的事件 ID，這將是後續查找具體修復程序的關鍵。

🛠️ 處置與修復指引
一旦您透過 `lseventlog` 指令識別出相關的事件 ID，請務必根據該事件 ID 查閱 IBM 官方的產品文件或支援網站，以獲取針對該特定事件的詳細修復程序。原廠未記載此處可直接提供通用修復步驟，唯一的官方認證實施步驟是根據事件日誌中的具體事件 ID 來執行對應的修復程序。

**一般性建議 (非特定事件 ID 的通用指引)**：
*   **檢查節點狀態**：使用 `lsnode` 指令檢查所有節點的狀態，確保所有節點均處於線上且健康狀態。
*   **檢查快取狀態**：雖然沒有直接的 CLI 指令來「清除」釘選資料，但確保系統軟體版本是最新的，有助於解決已知的快取管理問題。
*   **聯繫 IBM 支援**：如果事件日誌中的修復程序未能解決問題，或您無法找到對應的修復程序，請收集事件日誌和系統狀態資訊，並聯繫 IBM 技術支援以獲得進一步的協助。

[來源: svc_bkmap_cliguidebk.pdf, 第 1008 頁]

---

### [18/30] 錯誤碼: `CMMVC5786E` - 達到系統支援之最大磁區 (Volume) 數量上限 (FS5045)

**提問內容**：`FS5045 執行命令得到了一個錯誤訊息 CMMVC5786E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 950) (p.1), svc_bkmap_cliguidebk.pdf (p.845), web_72fa117b6f (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC5786E` 錯誤訊息明確指出，此操作失敗是因為叢集處於不穩定狀態。當 IBM Storage Virtualize 叢集不穩定時，任何需要叢集穩定狀態才能執行的操作都將失敗。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **錯誤訊息解讀**: 根據 IBM 官方參考手冊，針對 `CMMVC5786E` 錯誤，原廠明確記載「使用者回應 (User response): Not applicable」。這表示此錯誤本身並無直接的 CLI 指令可供「回應」或「修復」，而是需要解決導致叢集不穩定的根本原因。
2.  **通用診斷限制**: 由於此錯誤為叢集整體不穩定，診斷需聚焦於確認叢集各節點、服務與連線的健康狀態。然而，**經檢索現有參考技術資料，並未提供針對此類一般性叢集不穩定狀態的通用診斷 CLI 指令集**。
3.  **特定情境診斷 (若與 Remote Copy 相關)**: 若您執行命令並收到 `CMMVC5786E` 錯誤的操作與 Remote Copy 或夥伴關係 (Partnership) 相關，則可參考以下指令進行初步排查：
    *   **檢視夥伴關係狀態**:
        ```bash
        lspartnership
        lspartnershipcandidate
        ```
        ⚙️ 核心參數詳細說明表

---

### [19/30] 錯誤碼: `CMMVC5998E` - 設定之 IP 位址已被網路中其他設備佔用 (FS5200)

**提問內容**：`FS5200 執行命令得到了一個錯誤訊息 CMMVC5998E 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [20/30] 錯誤碼: `CMMVC6120E` - 節點機匣離線 (Node Canister Offline) (FS7200)

**提問內容**：`FS7200 執行命令得到了一個錯誤訊息 CMMVC6120E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 986) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC6120E Target is not the configuration node` 錯誤訊息表示您嘗試執行的命令必須在叢集系統 (cluster system) 的配置節點 (configuration node) 上執行，但您目前連線的節點並非該配置節點。此為 IBM Storage Virtualize 系統的設計限制，確保叢集配置的一致性與完整性，而非硬體故障。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **確認目前連線的節點是否為配置節點：**
    *   使用 `lsnode` 命令列出叢集中的所有節點。
    *   檢查 `config_node` 欄位，其值為 `yes` 的節點即為配置節點。

    ```bash
    lsnode
    ```
    ⚙️ 核心參數詳細說明表
    | 參數 | 說明 |
    | :--- | :--- |
    | `id` | 節點的唯一 ID。 |
    | `name` | 節點的名稱。 |
    | `config_node` | 指示該節點是否為配置節點 (`yes` 或 `no`)。 |
    | `state` | 節點的狀態。 |

2.  **若目前連線的節點不是配置節點：**
    *   您需要重新連線到被標記為 `config_node yes` 的節點，然後再執行您原先的命令。

🛠️ 處置與修復指引

此錯誤訊息的處置方式並非修復硬體故障，而是調整操作方式以符合系統的邏輯限制。

1.  **重新連線至配置節點：**
    *   根據 `lsnode` 命令的輸出，識別出 `config_node` 欄位為 `yes` 的節點。
    *   透過 SSH 或管理 GUI 重新連線到該配置節點的 IP 位址或主機名稱。
    *   在配置節點上重新執行您原先的命令。

⚠️ 安全注意事項與風險警告

*   在執行任何配置更改命令之前，請務必確認您已連線到正確的配置節點。在非配置節點上嘗試執行配置命令將會持續收到此錯誤。
*   IBM 官方參考手冊未記載此錯誤有其他過渡方式或繞過方法，唯一官方認證實施步驟為連線至配置節點執行相關命令。

🔍 執行後狀態驗證指令

在重新連線到配置節點並成功執行命令後，請使用相關的 `ls` 命令來驗證您的操作是否已成功生效。例如，如果您嘗試更改某個物件的屬性，請使用 `lsobject` 命令來確認更改。

---
[來源: svc_bkmap_cliguidebk.pdf, 第 986 頁]

---

### [21/30] 錯誤碼: `CMMVC6234E` - 磁碟插槽與指定磁碟類型 (NVMe/SAS) 不相容 (FS5200)

**提問內容**：`FS5200 執行命令得到了一個錯誤訊息 CMMVC6234E 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [22/30] 錯誤碼: `CMMVC6512E` - 系統安全憑證 (SSL/TLS Certificate) 已過期或無效 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC6512E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1024) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC6512E` 錯誤訊息表示您嘗試在單一指令中同時執行「建立新的仲裁磁碟 (quorum disk)」與「將該新磁碟設定為啟用 (active)」這兩個操作。IBM Storage Virtualize 系統設計上不允許在同一個指令中完成這兩項任務。

📋 Step-by-Step 樹狀診斷步驟與排查指令

此錯誤並非硬體故障，而是指令邏輯限制。系統明確指出，建立仲裁磁碟與啟用仲裁磁碟必須分開執行。

🛠️ 處置與修復指引

根據 IBM 官方參考手冊，解決此錯誤的唯一官方認證實施步驟如下：

1.  **第一步：建立新的仲裁磁碟。**
    *   您必須先提交一個指令來建立新的仲裁磁碟。
    *   請等待此任務完成。

2.  **第二步：啟用新的仲裁磁碟。**
    *   在建立仲裁磁碟的任務完成後，再提交一個指令來啟用該新的仲裁磁碟。

💻 概念性 CLI 設定流程與核心指令

以下為根據錯誤說明所推導出的概念性 CLI 步驟。請注意，具體的 `mkquorumdisk` 和 `addquorumdisk` 或 `setquorumdisk` 等指令參數，應查閱您當前 FlashSystem 9500 韌體版本的 IBM Storage Virtualize Command-Line Interface User's Guide 以獲取精確語法。

```bash
# 步驟一：建立新的仲裁磁碟
# 範例指令 (請替換為實際的儲存池ID和磁碟組件)
# mkquorumdisk -mdiskgroup <mdisk_group_id> -mdisk <mdisk_id>

# 假設您要將 MDisk 100 設定為仲裁磁碟，且該 MDisk 位於 MDisk Group 0
mkquorumdisk -mdiskgroup 0 -mdisk 100

# 等待上述指令執行完成並確認仲裁磁碟已建立。
# 您可以使用 lsquorumdisk 指令來查看當前的仲裁磁碟狀態。
lsquorumdisk

# 步驟二：啟用新的仲裁磁碟
# 範例指令 (請替換為實際的仲裁磁碟ID)
# addquorumdisk -active <quorum_disk_id>

# 假設您剛建立的仲裁磁碟 ID 為 0
addquorumdisk -active 0
```

⚙️ 核心參數詳細說明表

| 參數/指令 | 說明                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
| `mkquorumdisk` | 用於建立新的仲裁磁碟。 |

---

### [23/30] 錯誤碼: `CMMVC6601E` - PBR 複製原則無法套用 (RPO=0 且網路延遲過高) (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC6601E 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [24/30] 錯誤碼: `CMMVC7001E` - FlashSystem Grid 協調者 (Coordinator) 節點無法連通 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC7001E 該怎麼處理？`

**官方引述出處**：無

**系統專家解答輸出**：

【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。

💡 **建議線上確認方式 (CLI)**：
- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`
- 開機硬碟狀態查詢：`lsbootdrive`
- 系統事件與錯誤查詢：`lseventlog`
- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`

---

### [25/30] 錯誤碼: `CMMVC7005E` - Storage Partition 儲存分區超過分配容量上限 (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC7005E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1043) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC7005E` 錯誤訊息表示您所提交的命令無法執行，因為您指定的 I/O 群組目前沒有任何機箱 (enclosure) 與其關聯。這並非硬體故障，而是命令語法或架構配置上的邏輯限制。系統偵測到您嘗試對一個未綁定機箱的 I/O 群組執行操作。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認現有 I/O 群組與機箱的關聯性**：
    *   使用 `lsenclosure` 命令來列出所有現有的機箱及其所屬的 I/O 群組。這將幫助您識別哪些 I/O 群組已經有相關聯的機箱。

    ```bash
    lsenclosure
    ```

🛠️ 處置與修復指引
根據 `CMMVC7005E` 的官方說明，您需要：
1.  **指定正確的 I/O 群組**：在執行命令時，請確保您指定的 I/O 群組是已經有至少一個機箱與其關聯的。
2.  **確認機箱配置**：若您預期某個 I/O 群組應該有相關聯的機箱但 `lsenclosure` 命令顯示沒有，則需要檢查機箱的配置狀態，確保其已正確地被系統識別並分配到目標 I/O 群組。

[來源: svc_bkmap_cliguidebk.pdf, 第 1043 頁]

---

### [26/30] 錯誤碼: `CMMVC7010E` - 加入 FlashSystem Grid 失敗 (憑證 Truststore 交換異常) (FS9500)

**提問內容**：`FS9500 執行命令得到了一個錯誤訊息 CMMVC7010E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 1044) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC7010E` 錯誤訊息表示您嘗試執行的命令，其目標 MDisk (受管磁碟) 的模式設定為 `Array`。此命令要求選定的 MDisk 必須是 SAN MDisk (即非由本機磁碟組成的陣列 MDisk)。

簡而言之，您選定的 MDisk 是由儲存系統內部磁碟組成的陣列，而非從外部 SAN 映射進來的 MDisk，而您執行的命令不支援對 `Array` 模式的 MDisk 進行操作。這是一個命令邏輯限制，而非硬體故障。

📋 Step-by-Step 樹狀診斷步驟與排查指令

1.  **確認 MDisk 模式：**
    首先，您需要列出系統中的所有 MDisk，並檢查其模式。

    ```bash
    lsmdisk
    ```

    ⚙️ 核心參數詳細說明表

    | 參數 | 說明                                     |
    | :--- | :--------------------------------------- |
    | 無   | 列出所有 MDisk 的詳細資訊，包括其模式。 |

    🔍 執行後狀態驗證指令
    執行 `lsmdisk` 後，請仔細檢視輸出結果中的 `mode` 欄位。您會看到部分 MDisk 的模式為 `array`，而其他 MDisk 的模式可能為 `managed` 或 `unmanaged` (對於 SAN MDisk)。

🛠️ 處置與修復指引

根據 `CMMVC7010E` 的解釋與使用者回應，唯一的官方處置方式是：

1.  **識別正確的 MDisk：**
    使用 `lsmdisk` 命令的輸出結果，找到一個模式 (mode) 不是 `array` 的 MDisk。這些 MDisk 通常是從外部 SAN 映射進來的，或是在 Storage Virtualize 層級創建的儲存池中的 MDisk。

2.  **重新執行命令：**
    針對您識別出的、模式非 `array` 的 MDisk，重新提交您原先嘗試執行的命令。

⚠️ 安全注意事項與風險警告
在執行任何命令之前，請務必確認您選定的 MDisk 是正確的目標，以避免對生產資料造成不必要的影響。若不確定 MDisk 的用途，請諮詢您的儲存管理員或 IBM 技術支援。

[來源: svc_bkmap_cliguidebk.pdf, 第 1044 頁]

---

### [27/30] 錯誤碼: `CMMVC5920E` - 可用磁碟數量不足無法建立指定 RAID/DRAID (FS5200)

**提問內容**：`FS5200 執行命令得到了一個錯誤訊息 CMMVC5920E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 967) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
錯誤訊息 `CMMVC5920E` 指出 FlashCopy 映射未能建立，原因在於所涉及的 FlashCopy 一致性群組 (consistency group) 並非處於閒置 (idle) 狀態。這是一個架構邏輯上的限制，而非硬體故障。FlashCopy 映射的建立或修改，要求其所屬的一致性群組必須處於閒置狀態，以確保資料的一致性與操作的完整性。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **確認一致性群組狀態**：
    *   首要步驟是確認導致此錯誤的 FlashCopy 一致性群組的當前狀態。
    *   請查閱 IBM Storage Virtualize 官方 Command Line Interface User's Guide，以獲取查詢 FlashCopy 一致性群組狀態的正確 CLI 指令。該指令通常會顯示群組的名稱、ID 以及其當前狀態（例如 `idle`、`copying`、`stopping` 等）。
    *   **嚴禁自行推測或捏造指令**：由於參考資料中未提供查詢 FlashCopy 一致性群組狀態的具體 CLI 指令，因此無法在此處提供。請務必參考您當前系統版本對應的 IBM 官方手冊。

🛠️ 處置與修復指引
1.  **停止 FlashCopy 一致性群組**：
    *   若經查詢，該 FlashCopy 一致性群組的狀態並非 `idle` (例如處於 `copying` 或 `stopping` 狀態)，則必須先停止該一致性群組的操作，使其轉換至 `idle` 狀態。
    *   請查閱 IBM Storage Virtualize 官方 Command Line Interface User's Guide，以獲取停止 FlashCopy 一致性群組的正確 CLI 指令。
    *   **嚴禁自行推測或捏造指令**：同上，請務必參考您當前系統版本對應的 IBM 官方手冊。
2.  **等待狀態轉換**：
    *   執行停止操作後，請再次查詢一致性群組的狀態，確認其已成功轉換為 `idle`。此過程可能需要一些時間。
3.  **重新執行 FlashCopy 映射建立命令**：
    *   一旦確認 FlashCopy 一致性群組處於 `idle` 狀態，即可重新執行原先失敗的 FlashCopy 映射建立命令。

**重要提示**：
*   IBM 官方文件對 `CMMVC5920E` 的「User response」標註為「Not applicable」，這進一步印證了此錯誤是因系統邏輯狀態不符操作要求所致，需要透過調整相關物件的狀態來解決，而非直接修改命令參數或處理硬體故障。
*   所有操作務必遵循 IBM 官方文件記載的步驟與指令，以確保系統穩定性與資料完整性。

---

### [28/30] 錯誤碼: `CMMVC5935E` - 熱備援磁碟 (Spare Drive) 無法分配至陣列 (FS5000)

**提問內容**：`FS5000 執行命令得到了一個錯誤訊息 CMMVC5935E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 968) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析

`CMMVC5935E` 錯誤訊息表示您嘗試執行的命令中，所指定的物件不存在。這是一個命令語法或邏輯層面的錯誤，而非硬體故障。系統無法找到您在命令中引用的特定儲存物件（例如：VDisk、MDisk、主機、埠、節點等）。

📋 Step-by-Step 樹狀診斷步驟與排查指令

此錯誤的根本原因在於命令中指定的物件識別碼或名稱不正確，或該物件已被刪除。請依照以下步驟進行診斷：

1.  **確認原始命令與物件名稱/ID**：
    *   首先，請回顧您執行時收到 `CMMVC5935E` 錯誤的完整 CLI 命令。
    *   仔細檢查命令中所有物件的名稱或 ID 是否拼寫正確，且大小寫是否符合系統要求（通常區分大小寫）。

2.  **驗證物件是否存在**：
    *   根據您原始命令中嘗試操作的物件類型，使用對應的 `ls` 命令來確認該物件是否確實存在於系統中。以下是一些常用物件的查詢指令：

    ```bash
    # 查詢 VDisk (虛擬磁碟)
    lsvdisk

    # 查詢 MDisk (受管磁碟)
    lsmdisk

    # 查詢 Host (主機)
    lshost

    # 查詢 Port (光纖通道或 iSCSI 埠)
    lsportfc
    lsportip

    # 查詢 Node (節點)
    lsnode

    # 查詢 Array (陣列)
    lsarray

    # 查詢 Pool (儲存池)
    lsmdiskgrp
    ```
    *   請仔細比對 `ls` 命令的輸出結果，確認您在原始命令中使用的物件名稱或 ID 是否與系統中實際存在的物件完全一致。

🛠️ 處置與修復指引

根據 `CMMVC5935E` 的官方解釋，使用者回應為「指定正確的物件，然後重新提交命令」。 因此，處置方案如下：

1.  **修正物件名稱/ID**：
    *   在執行了上述的 `ls` 查詢指令後，您應該已經確認了正確的物件名稱或 ID。
    *   請使用正確的物件名稱或 ID 修正您的原始命令。
    *   例如，如果您嘗試刪除一個名為 `vdisk001` 的 VDisk，但系統中實際存在的 VDisk 名為 `vdisk_prod_001`，則您需要將命令修正為 `rmvdisk vdisk_prod_001`。

2.  **重新提交命令**：
    *   使用修正後的命令重新提交。

**⚠️ 安全注意事項與風險警告**

*   在執行任何修改系統配置的命令之前，請務必仔細核對命令中的所有參數，特別是物件名稱或 ID，以避免誤操作。
*   若不確定物件的正確名稱或 ID，請務必先使用 `ls` 系列指令進行查詢確認。

---

### [29/30] 錯誤碼: `CMMVC6150E` - IP Quorum 仲裁設備離線或連線超時 (SVC)

**提問內容**：`SVC 執行命令得到了一個錯誤訊息 CMMVC6150E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 990) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6150E` 錯誤訊息明確指出您所輸入的指令中，指定的 `ACTION`（動作）參數無效。這並非硬體故障，而是指令語法或參數使用不正確所導致的邏輯限制。

📋 Step-by-Step 樹狀診斷步驟與排查指令
1.  **檢視原始指令**: 請仔細檢查您執行時收到 `CMMVC6150E` 錯誤的完整 CLI 指令。
2.  **識別無效動作**: 根據錯誤訊息，問題點在於指令中的 `ACTION` 部分。請確認您嘗試執行的具體動作或子命令。
3.  **查閱官方手冊**: 針對您嘗試執行的特定指令，請查閱 IBM Storage Virtualize 或 FlashSystem 相關型號的官方 CLI 指令參考手冊。
    *   確認該指令的正確語法。
    *   確認該指令支援的所有有效 `ACTION` 參數及其定義。
    *   確認您使用的 `ACTION` 是否適用於當前的系統狀態或物件。

🛠️ 處置與修復指引
1.  **修正指令**: 根據官方手冊的指引，修正您指令中無效的 `ACTION` 參數，替換為一個有效的動作。
2.  **重新執行**: 修正後，請重新提交該指令。

[來源: svc_bkmap_cliguidebk.pdf, 第 990 頁]

---

### [30/30] 錯誤碼: `CMMVC6200E` - 機箱電源供應器 (PSU) 故障或未通電 (FS7300)

**提問內容**：`FS7300 執行命令得到了一個錯誤訊息 CMMVC6200E 該怎麼處理？`

**官方引述出處**：svc_bkmap_cliguidebk.pdf (Page 993) (p.1)

**系統專家解答輸出**：

🚨 故障根本原因分析
`CMMVC6200E` 錯誤訊息表示探索程序未在預設時間限制內完成。

📋 Step-by-Step 樹狀診斷步驟與排查指令
經檢索 IBM 官方參考手冊，針對 `CMMVC6200E` 錯誤，原廠未記載此錯誤的具體診斷步驟或可由使用者執行的排查指令。

🛠️ 處置與修復指引
根據 IBM 官方參考手冊的指示，當遇到 `CMMVC6200E` 錯誤時，唯一官方認證的處置步驟為聯繫 IBM 支援服務。

[來源: svc_bkmap_cliguidebk.pdf, 第 993 頁]

---
