import json
from vector_store import add_chunks_to_db

chunks = [
    {
        "id": "manual_ibm_docs_table1_fs7200_ru",
        "content": "IBM FlashSystem 7200 / 7300 官方控制機匣可更換零件清單 (IBM Docs Table 1. Control enclosure replaceable units 9.1.0 官方原文): 1. 01YM315: Trusted program module (TPM) - 適用於 FS7200/FS7300 Node Canister 的信任程式模組 (Trusted Platform/Program Module). 2. 01YM314: Power interposer (電源中介轉換板). 3. 01YM285: 25 Gbps dual-port iSCSI (iWARP) adapter (雙埠 25G iSCSI 介面卡). 4. 01FT777: 25 Gbps SFP28 (RoCE) 光纖收發模組. 5. 00RY190: 16 Gbps FC short-wave (SW) SFP 光纖收發模組. 6. 00RY191: 16 Gbps FC long-wave (LW) SFP 光纖收發模組. 7. 00RY543: CR 2032 coin cell (主機板 CR2032 水銀電池). 8. 00AR240: Left OEM bezel (左側 OEM 面蓋). 9. 00AR241: Right OEM bezel (右側 OEM 面蓋). 10. 00Y2512: SFF Enclosure IBM branded bezel, right (右側 IBM 品牌面蓋). 官方線上驗證指令: lsnodevpd <node_id> (檢視節點 VPD/TPM 料號), lsdrive <drive_id> (檢視硬碟 FRU_part_number), lsbootdrive, sainfo lsservicestatus.",
        "metadata": {
            "source": "IBM_Docs_FS7200_Replaceable_Units_Table1_9.1.0.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.0?topic=ru-control-enclosure-replaceable-units"
        }
    },
    {
        "id": "manual_research_03NK551",
        "content": "FS7300 / FS5200 / FS5300 7.68 TB 2.5-inch NVMe Flash Drive Part Number (FRU): 03NK551 (主要更換料號). 其他相容料號: 03JK467. Feature Code: AG0F. (FS9500 4U 專用料號為 03JK376). 線上確認指令: lsdrive <drive_id> 查看 FRU_part_number 欄位.",
        "metadata": {
            "source": "IBM_Replaceable_Units_FS7300_Drives.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable"
        }
    },
    {
        "id": "manual_fru_m2_ssd_240gb",
        "content": "IBM FlashSystem 7300 / 7200 / 5200 / 5300 / 9200 / SVC 零件料號: 240 GB M.2 SSD (開機磁碟 / Boot Drive / NVMe M.2 SSD). 主要 FRU Part Number: 01LJ207. 相容/替代 FRU 料號: 02WF311. 480 GB M.2 SSD 料號: 02WF312. 用途說明: 安裝於 Node Canister 主機板上的 M.2 NVMe SSD，用於存放系統開機映像檔與 Dump space 中繼資料。線上確認指令: lsbootdrive, lsnodevpd <node_id>, sainfo lsservicestatus.",
        "metadata": {
            "source": "IBM_Replaceable_Units_FS7300_BootDrive.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable"
        }
    },
    {
        "id": "manual_fru_fc_adapter_32gb",
        "content": "Quad-port 32 Gbps FC adapter (PCIe Gen4 四埠 32 Gbps Fibre Channel 主機介面卡 Host Interface Adapter). Feature Code: ACH2 (Shortwave 光纖) / ACH3 (Longwave 光纖). 主要 FRU Part Number: 02CL193 / 01PG587. 12 Gbps 4-Port SAS Adapter 料號: 01PE894 / 02CL195 (FC: ACH0). 25 Gbps 2-Port RoCE Adapter 料號: 02CL194 (FC: ACH1). 適用機型: FlashSystem 5200, 5300, 7300, 9500, SVC SV2/SV3. 插槽位置: Node Canister PCIe Slot 1 或 Slot 2. 線上確認指令: lsnodevpd <node_id>, sainfo lsservicestatus.",
        "metadata": {
            "source": "IBM_Replaceable_Units_Adapters.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable"
        }
    },
    {
        "id": "manual_cmmvc_1035e",
        "content": "CMMVC1035E: The command failed because the volume received I/O within the defined volume protection period. 錯誤原因: 系統啟用了磁碟保護功能 (Volume Protection)。當管理者執行刪除磁碟 (rmvolume)、還原或覆蓋操作時，若該磁碟在 vdisk_protection_time 設定的保護時間內 (例如 15 分鐘) 仍有 I/O 活動，系統會攔截拒絕以防誤刪線上生產資料。處置步驟: 1. 停止主機 I/O 並等待超過保護時間 (透過 lssystem 查看 vdisk_protection_time) 後重試。 2. 若確認安全且需緊急執行，可使用 chsystem -vdiskprotectionenabled no 暫時停用保護，執行完後以 chsystem -vdiskprotectionenabled yes 重新啟用。 3. 檢查主機映射 lsvdiskhostmap 並在必要時解除映射 rmvdiskhostmap。",
        "metadata": {
            "source": "IBM_CLI_Messages_Reference_CMMVC.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.x?topic=messages-command-line-interface"
        }
    },
    {
        "id": "manual_cmmvc_1026e",
        "content": "CMMVC1026E: The command failed because the host cannot have a specific I/O group assigned to it, as the host is associated with a storage partition. 錯誤原因: 該主機 (Host) 目前已關聯至特定的儲存分區 (Storage Partition) 或擁有權群組 (Ownership Group)。在多租戶儲存分區機制下，為維持分區隔離與配置一致性，系統禁止手動將該主機指派給非該分區規範的特定 I/O Group。處置步驟: 1. 透過 lshost <host_id> 與 lsownershipgroup / lsstoragepartition 檢視主機所屬分區與可用資源。 2. 若為多系統環境，確保在 Storage Partition 的 Active Management System 上操作。 3. 由分區管理者在 Storage Partition 層級納入該 I/O Group，或先將主機移出 Storage Partition 後再單獨指派。",
        "metadata": {
            "source": "IBM_CLI_Messages_Reference_CMMVC.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.x?topic=messages-command-line-interface"
        }
    },
    {
        "id": "manual_cmmvc_8000e",
        "content": "CMMVC8000E: The parameter is not valid or not recognized. 錯誤原因: 執行的 CLI 指令中包含無法辨識、拼寫錯誤或與當前機型/軟體版本不相容的參數與選項 (如參數多打底線、大小寫誤用、或該命令在特定物件模式下不支援該 flag)。處置步驟: 1. 檢查指令語法與拼寫。 2. 線上調用 help <command_name> (例如 help chvolume) 查看官方正確參數。 3. 修正後重新執行命令。",
        "metadata": {
            "source": "IBM_CLI_Messages_Reference_CMMVC.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.x?topic=messages-command-line-interface"
        }
    },
    {
        "id": "manual_flashsystem_grid_managegrid",
        "content": "FlashSystem Grid 命令列設定與管理 (managegrid CLI): 1. 建立 FlashSystem Grid (Coordinator 協調者系統): 在主系統執行 managegrid -create -name <GridName> (例如 managegrid -create -name FS_Grid)。此系統成為 Grid Coordinator。 2. 配置安全信任憑證 (Truststore): 檢視並導出 Member 系統憑證 lssystemcertstore，並在 Coordinator 上透過 mktruststore -file <member_cert.pem> 匯入信任庫。 3. 將成員系統加入 Grid: 執行 managegrid -join -system <member_system_name_or_ip>。 4. Grid 狀態與成員檢視: lsgrid (檢視 Grid 摘要), lsgridmembers (列出所有 Grid 成員系統), lsgridsystem (檢視 Grid 系統資訊), lsgridpartition (檢視 Grid 儲存分區)。 5. 維護與切換: managegrid -makecoordinator (切換/提升新協調者), managegrid -leave (主動退出 Grid), managegrid -remove -system <system_name> (移除指定成員)。",
        "metadata": {
            "source": "IBM_FlashSystem_Grid_Commands_Reference.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.x?topic=commands-managegrid"
        }
    },
    {
        "id": "manual_fs5000_family_ru_full",
        "content": "IBM FlashSystem 5000 系列 (FS5015, FS5035, FS5045, FS5200, FS5300, FS5600) 官方零件料號與組件清單 (Replaceable Units): 1. FS5200/5300/5600 1U NVMe 控制機箱: 240 GB M.2 NVMe Boot SSD (FRU: 01LJ207, 02WF311), 480 GB M.2 SSD (02WF312). 7.68 TB NVMe Drive (FRU: 03NK551, 03JK467, FC: AG0F). 1.92TB (03NK548), 3.84TB (03NK549), 15.36TB (03NK552), 30.72TB (03NK553). FCM Gen2/Gen3/Gen4 (4.8TB: 03NK482, 9.6TB: 03NK483, 19.2TB: 03NK484, 38.4TB: 03NK485). 介面卡: 32G 4-Port FC Adapter (FRU: 02CL193/01PG587, FC: ACH2/ACH3), 12G 4-Port SAS Adapter (FRU: 01PE894/02CL195, FC: ACH0), 25GbE RoCE (02CL194, FC: ACH1). 2000W AC Redundant PSU, 4x Fan Modules per Canister. 2. FS5015/5035/5045 2U SAS 機箱: 1.92TB/3.84TB/7.68TB/15.36TB 2.5\" SAS SSD, 1.2TB/2.4TB 10K SAS HDD, 8TB-18TB NL-SAS HDD, 800W/1200W AC PSU. 線上確認指令: lsnodevpd <node_id>, lsdrive <drive_id>, lsbootdrive.",
        "metadata": {
            "source": "IBM_Docs_FS5000_Family_Replaceable_Units.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-5x00/9.1.x?topic=ru-control-enclosure-replaceable-units"
        }
    },
    {
        "id": "manual_fs9000_family_ru_full",
        "content": "IBM FlashSystem 9000 系列 (FS9100, FS9200, FS9500, FS9600) 官方零件料號與組件清單 (Replaceable Units / FRU Table): 1. FS9500 4U 高效能控制機箱 (4666-AH8/UH8): 7.68 TB NVMe Drive (FRU: 03JK376). 1.92TB, 3.84TB, 15.36TB, 30.72TB 2.5\" NVMe SSD. FlashCore Module Gen3/Gen4 (4.8TB, 9.6TB, 19.2TB, 38.4TB FCM). 32 Gbps 4-Port FC Adapter, 64 Gbps FC Adapter, 100 Gbps 2-Port RoCE Ethernet Adapter. 4 組 2400W AC Redundant PSU (2+2 備援), 高風量熱插拔散熱風扇模組, M.2 NVMe Boot SSD. 2. FS9200 2U 控制機箱 (9846/9848-UG8): 240 GB M.2 NVMe Boot SSD (FRU: 01LJ207, 02WF311), 32GB/64GB DDR4 DIMM (01LJ207), 32G FC Adapter (02CL193). 線上確認指令: lsnodevpd <node_id>, lsdrive <drive_id>, lsbootdrive, sainfo lsservicestatus.",
        "metadata": {
            "source": "IBM_Docs_FS9000_Family_Replaceable_Units.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/flashsystem-9x00/9.1.x?topic=ru-control-enclosure-replaceable-units"
        }
    },
    {
        "id": "manual_svc_family_ru_full",
        "content": "IBM SAN Volume Controller (SVC 2145-SV1, 2145-SV2, 2145-SV3, 2147-SV2, 2147-SV3) 官方零件料號清單 (Replaceable Units): 1. SVC SV2/SV3 節點硬體: 240 GB M.2 NVMe SSD Boot Drive (FRU: 01LJ207, 02WF311), 32GB/64GB/128GB DDR4 ECC DIMM. 32 Gbps 4-Port FC Host Interface Adapter (FRU: 02CL193, 01PG587), 25GbE 2-Port / 100GbE RoCE 介面卡. 雙冗餘熱插拔電源供應器 (PSU), 散熱風扇模組. 2. 功能用途: 虛擬化儲存節點開機、快取傾印中繼資料保護與光纖 SAN 路由轉發. 線上確認指令: lsnodevpd <node_id>, lsbootdrive, sainfo lsservicestatus.",
        "metadata": {
            "source": "IBM_Docs_SVC_Family_Replaceable_Units.md",
            "page": 1,
            "type": "web",
            "url": "https://www.ibm.com/docs/en/sanvolumecontroller/9.1.x?topic=ru-replaceable-units"
        }
    }
]

add_chunks_to_db(chunks)
print(f"成功注入 {len(chunks)} 筆官方手冊 Chunks 至知識庫！")




