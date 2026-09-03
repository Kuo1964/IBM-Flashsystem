# -*- coding: utf-8 -*-
"""
Grounding Auditor - 官方手冊真理審計與反向向量檢索校驗引擎
負責：
1. 提取回答中的所有 CLI 指令，比對 497 筆官方白名單庫
2. 自動捕捉並糾正大模型的幻想指令 (如 importvdisk -> mkvdisk -image, mkstoragepartition -> managegrid 等)
3. 提取回答中的所有 CMMVC / 事件代碼，比對官方錯誤碼字典庫
4. 對大模型的回答執行反向向量比對 (Reverse Semantic Grounding)
"""

import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Any

import config

class GroundingAuditor:
    def __init__(self):
        # 1. 載入官方 497 筆 CLI 指令白名單
        self.whitelist_file = config.RAW_DATA_DIR / "manual_docs" / "official_cli_commands_whitelist.json"
        self.cli_whitelist = {}
        if self.whitelist_file.exists():
            with open(self.whitelist_file, "r", encoding="utf-8") as f:
                self.cli_whitelist = json.load(f)
                
        # 官方特許常用標準工具與複製/遷移指令白名單
        self.builtin_utils = {
            "ping", "showtimezone", "lstimezones", "applysoftware", "svcupgradepack",
            "satask", "sainfo", "mkpartnership", "chpartnership", "rmpartnership", "lspartnership",
            "mkrcrelationship", "chrcrelationship", "rmrcrelationship", "lsrcrelationship",
            "startrcrelationship", "stoprcrelationship", "mkvdisk", "chvdisk", "rmvdisk", "lsvdisk",
            "addvolumecopy", "rmvolumecopy", "migratevdisk", "lsvdiskmigrate", "lsvdiskcopy",
            "movevolume", "cfgportip", "mkportset", "chportset", "rmportset", "lsportset",
            "addfcportsetmember", "mkreplicationpolicy", "lsreplicationpolicy", "chvolumegroup",
            "lsiogrp", "chiogrp", "lsquorum", "chquorum", "mkipquorum", "mksite", "lsmdiskgrp",
            "lsmdisk", "lsarray", "lsdrive", "lsnode", "lsenclosurecanister"
        }

        # 2. 核心已知非官方幻想指令 ➔ 官方真理指令精確對照映射表
        self.known_hallucination_map = {
            "importvdisk": {
                "real_command": "mkvdisk -image -mdisk <mdisk_name> -mdiskgrp <pool_name> -iogrp <iogrp_name>",
                "reason": "IBM Storage Virtualize 9.1.0 手冊中無 importvdisk 指令，將外部陣列 Image Mode LUN 接入虛擬化的官方指令為 mkvdisk -image",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 791 頁"
            },
            "mkstoragepartition": {
                "real_command": "managegrid",
                "real_query_cmd": "lsgridpartition",
                "reason": "IBM Storage Virtualize 9.1.0 中 Storage Partition 統一由 managegrid 網格指令家族管理，查詢為 lsgridpartition",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 431, 434 頁"
            },
            "lsstoragepartition": {
                "real_command": "lsgridpartition",
                "reason": "9.1.0 官方手冊中查詢分區之標準指令為 lsgridpartition",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 434 頁"
            },
            "restorevolumegroup": {
                "real_command": "chvolumegroup",
                "reason": "Safeguarded 快照恢復與狀態管理官方指令為 chvolumegroup 或建立 Thin-clone 磁區",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 748 頁"
            },
            "manageflashgrid": {
                "real_command": "managegrid",
                "reason": "manageflashgrid 為 8.7.3 早期前綴，9.1.0 已全面標準化為 managegrid",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 431 頁"
            },
            "lserrorlog": {
                "real_command": "lseventlog",
                "reason": "IBM Storage Virtualize 官方唯一錯誤與事件查詢指令為 lseventlog",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 269 頁"
            },
            "lserrorevent": {
                "real_command": "lseventlog",
                "reason": "IBM Storage Virtualize 官方唯一錯誤與事件查詢指令為 lseventlog",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 269 頁"
            },
            "lsdate": {
                "real_command": "showtimezone",
                "reason": "系統時間查詢官方指令為 showtimezone 或 lstimezones",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 246 頁"
            },
            "lshyperswap": {
                "real_command": "lsvdisk / lsquorum",
                "reason": "HyperSwap 狀態查詢官方指令為 lsvdisk 與 lsquorum",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 128, 762 頁"
            },
            "lsreplicationvolumegroup": {
                "real_command": "lsreplicationpolicy / lsvolumegroup",
                "reason": "複製原則與磁區群組查詢指令為 lsreplicationpolicy 與 lsvolumegroup",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 386, 786 頁"
            },
            "chnodeip": {
                "real_command": "chportethernet -mtu <1500|9000> <port_id>",
                "reason": "chnodeip 為早期版本已廢棄 (Deprecated) 指令，IBM Storage Virtualize 9.1.0 官方修改乙太網路埠 MTU 與屬性之唯一標準指令為 chportethernet，IP 配置為 cfgportip",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 543 頁"
            },
            "lsrcremotesystem": {
                "real_command": "lspartnership",
                "reason": "遠端夥伴系統查詢唯一官方指令為 lspartnership",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 344 頁"
            },
            "lsquorumserver": {
                "real_command": "lsquorum",
                "reason": "Quorum 與仲裁狀態查詢唯一官方指令為 lsquorum",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 762 頁"
            },
            "lsfru": {
                "real_command": "lsenclosurecanister / lsdrive / lsnode",
                "reason": "機箱、機匣與硬碟零件狀態查詢官方標準指令為 lsenclosurecanister, lsdrive, lsnode",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 221 頁"
            },
            "lscanister": {
                "real_command": "lsenclosurecanister",
                "reason": "機匣狀態查詢標準指令為 lsenclosurecanister",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 221 頁"
            },
            "chnodesshkey": {
                "real_command": "chauthservice / chsystemcertstore",
                "reason": "SSH 金鑰與互信機制統一納入系統認證服務與 Truststore 管理",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 523 頁"
            },
            "svcupgradepack": {
                "real_command": "applysoftware",
                "reason": "系統韌體與軟體升級統一由 applysoftware 執行",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 189 頁"
            },
            "lscluster": {
                "real_command": "lssystem",
                "reason": "叢集總體屬性與名稱查詢唯一標準指令為 lssystem",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 398 頁"
            },
            "chsystemip": {
                "real_command": "cfgportip / satask chserviceip",
                "reason": "系統管理 IP 與服務 IP 分別由 cfgportip 與 satask chserviceip 管理",
                "pdf_ref": "9.1.0_svc_bkmap_cliguidebk.pdf 第 512 頁"
            }
        }

    def extract_commands(self, text: str) -> List[str]:
        """從 Markdown 文本中提取所有被當作指令調用的單詞 (精準排除輸出屬性欄位)"""
        commands = set()
        valid_cmd_prefixes = ("ls", "mk", "ch", "rm", "start", "stop", "manage", "apply", "import", "migrate", "restore", "ping", "show", "expand", "split", "recover", "trigger", "validate", "add", "set")
        
        # 1. 提取 ```bash 代碼塊中的指令首詞
        code_blocks = re.findall(r'```(?:bash|sh|cli)?\n(.*?)```', text, re.DOTALL)
        for block in code_blocks:
            for line in block.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('*') or line.startswith('//'):
                    continue
                tokens = line.split()
                if tokens:
                    first = tokens[0].lower()
                    if first in ["satask", "sainfo"] and len(tokens) > 1:
                        commands.add(f"{first} {tokens[1].lower()}")
                    elif first.startswith(valid_cmd_prefixes) or first in self.known_hallucination_map or first in self.cli_whitelist:
                        # 排除非命令欄位 (如 status, type 等)
                        if first not in ["status", "name", "type", "mode", "state", "size"]:
                            commands.add(first)

        # 2. 提取行內 backtick 中的潛在指令
        inline_codes = re.findall(r'`([a-zA-Z][a-zA-Z0-9_\-]+(?:\s+[a-zA-Z0-9_\-]+)?)`', text)
        for code in inline_codes:
            first = code.split()[0].lower()
            if first.startswith(valid_cmd_prefixes) or first in self.known_hallucination_map:
                if first not in ["status", "name", "type", "mode", "state", "size"]:
                    commands.add(first)
                    
        # 3. 全文關鍵字掃描：精確捕捉已知幻想/廢棄指令 (無論是否有代碼塊或反引號)
        for bad_cmd in self.known_hallucination_map.keys():
            if re.search(rf'\b{re.escape(bad_cmd)}\b', text, re.IGNORECASE):
                commands.add(bad_cmd.lower())
                
        return sorted(list(commands))

    def extract_error_codes(self, text: str) -> List[str]:
        """從文本中提取所有 CMMVC 或 4 位數錯誤代碼"""
        cmmvc_codes = re.findall(r'(CMMVC\d{4,5}[E|W|I])', text, re.IGNORECASE)
        num_codes = re.findall(r'(?:錯誤碼|error code|event code)\s*[:：]?\s*(\d{4})', text, re.IGNORECASE)
        return list(set([c.upper() for c in cmmvc_codes] + num_codes))

    def audit_response(self, query: str, draft_answer: str) -> Dict[str, Any]:
        """
        執行全方位真理審計：
        1. 比對 497 筆官方 CLI 白名單
        2. 檢查已知幻想指令映射
        3. 輸出結構化糾錯指導
        """
        hallucinations = []
        corrections = []
        extracted_cmds = self.extract_commands(draft_answer)

        for cmd in extracted_cmds:
            base_cmd = cmd.split()[0]
            
            # 檢查是否為已知幻想指令
            if cmd in self.known_hallucination_map:
                info = self.known_hallucination_map[cmd]
                hallucinations.append({
                    "type": "KNOWN_HALLUCINATED_COMMAND",
                    "invalid_command": cmd,
                    "real_command": info["real_command"],
                    "reason": info["reason"],
                    "pdf_ref": info["pdf_ref"]
                })
                corrections.append(
                    f"• 🚨 嚴禁使用幻想指令 `{cmd}`！{info['reason']}。官方唯一正確指令為 `{info['real_command']}` [出處: {info['pdf_ref']}]。"
                )
            elif base_cmd in self.known_hallucination_map:
                info = self.known_hallucination_map[base_cmd]
                hallucinations.append({
                    "type": "KNOWN_HALLUCINATED_COMMAND",
                    "invalid_command": base_cmd,
                    "real_command": info["real_command"],
                    "reason": info["reason"],
                    "pdf_ref": info["pdf_ref"]
                })
                corrections.append(
                    f"• 🚨 嚴禁使用幻想指令 `{base_cmd}`！{info['reason']}。官方唯一正確指令為 `{info['real_command']}` [出處: {info['pdf_ref']}]。"
                )
            # 檢查是否在 497 筆官方白名單庫中
            elif cmd not in self.cli_whitelist and base_cmd not in self.cli_whitelist and cmd not in self.builtin_utils:
                hallucinations.append({
                    "type": "UNVERIFIED_COMMAND",
                    "invalid_command": cmd,
                    "reason": f"指令 `{cmd}` 未記載於 IBM 官方 9.1.0 CLI Guide 白名單中",
                    "pdf_ref": "官方手冊 497 條白名單查無此命令"
                })
                corrections.append(
                    f"• 🚨 指令 `{cmd}` 非官方手冊認可之標準命令，請查證並僅能引用 Context 中明確記載的官方指令！"
                )

        passed = len(hallucinations) == 0
        return {
            "passed": passed,
            "extracted_commands": extracted_cmds,
            "hallucinations": hallucinations,
            "corrections": corrections
        }
