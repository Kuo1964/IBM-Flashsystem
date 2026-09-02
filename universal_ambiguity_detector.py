# -*- coding: utf-8 -*-
"""
Universal Ambiguity & Architecture Clash Evaluator
通用架構矛盾與需求歧義動態評估器 (無需人工規則表，全自動動態辨析任意儲存架構衝突)
"""

import json
import re
import httpx
from typing import Dict, Any, List, Optional
import config

class UniversalAmbiguityDetector:
    CLASH_SYSTEM_PROMPT = """你是一位極度嚴謹的 IBM Storage Virtualize & FlashSystem 原廠首席架構師審查官。
請審查使用者的【技術提問】，並結合 IBM Storage Virtualize 官方手冊（101 本 PDF 及 9.1.0 CLI Guide）中的架構真理，動態判斷該提問是否存在以下 4 類架構矛盾或嚴重概念衝突：

1. 【版本生命週期矛盾 (VERSION_LIFECYCLE_CLASH)】：
   - 在已廢除該功能的版本中請求使用（例如：在 9.1.0+ 要求設定 Metro Mirror / Global Mirror，手冊記載 9.1.0 已由 PBR 全面取代）。
   - 在尚未引入該功能的舊版本中請求使用（例如：在 8.4 請求使用 FlashSystem Grid）。
2. 【硬體與物理邊界矛盾 (HARDWARE_BOUNDARY_CLASH)】：
   - 請求的配置超出該機型硬體規格（例如：在 FS5200 建立 4 節點叢集，原廠規定 1U 僅支援單機箱 2 節點；在 3 顆硬碟上建立 DRAID 6 陣列，DRAID 6 至少需 6 顆）。
   - 請求連接未配備介面卡的硬體（例如：在未插 SAS HBA 的 NVMe 機箱直連 SAS 擴充櫃）。
3. 【操作維度與機制混淆 (OPERATION_DIMENSION_CLASH)】：
   - 混合了兩個不同維度的操作（例如：將 NDVM/Volume Mobility「跨 I/O Group 控制器搬移」與「從 Pool0 搬到 Pool1 儲存池 Extent 搬移」混為一談）。
   - 誤將本機防勒索快照 Safeguarded Copy 當成跨站點遠端複製 (mkreplicationpolicy)。
4. 【關鍵前置條件衝突/缺失 (MISSING_PREREQUISITE_CLASH)】：
   - 跨站點複製未設定 IP/FC Portset 就直接建立 Partnership；未啟用 NPIV 虛擬化就指派虛擬 WWPN。

請以嚴格 JSON 格式輸出：
{
  "has_clash": true,
  "clash_type": "VERSION_LIFECYCLE | HARDWARE_BOUNDARY | OPERATION_DIMENSION | MISSING_PREREQUISITE | NONE",
  "clash_summary": "一句話總結矛盾焦點",
  "detailed_explanation": "精確指出提問中哪兩個概念或參數在 IBM 原廠規範中互相排斥",
  "official_sources": ["引用手冊名稱或章節，如 SG24-8542 Section 7.5, REDP-5654 等"],
  "branch_a": {
    "intent_desc": "情境 A：若使用者的真實目標為 X",
    "official_approach": "官方標準架構與核心指令"
  },
  "branch_b": {
    "intent_desc": "情境 B：若使用者的真實目標為 Y",
    "official_approach": "官方標準架構與核心指令"
  }
}
若提問毫無矛盾或需求非常明確，請輸出 {"has_clash": false}。
只輸出純 JSON，不要任何 Markdown 代碼塊標籤或額外文字。
"""

    @classmethod
    def evaluate_clash(cls, query_text: str) -> Dict[str, Any]:
        """動態評估使用者提問是否存在架構矛盾或概念衝突"""
        if not config.GEMINI_API_KEY:
            return {"has_clash": False}
            
        try:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
            prompt = f"{cls.CLASH_SYSTEM_PROMPT}\n\n【使用者提問】：{query_text}"
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 1024,
                    "responseMimeType": "application/json"
                }
            }
            
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(gemini_url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        txt = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                        clash_info = json.loads(txt)
                        return clash_info
        except Exception as e:
            print(f"[警告] 動態矛盾評估異常: {e}")
            
        return {"has_clash": False}
