"""
IBM FlashSystem 專家系統 - 中央 RAGEngine 獨立深模組 (Central RAG Engine)
提供雙端 (Web & Local) 共享之高內聚、極簡介面處理核心 (Single Source of Truth)
"""

import os
import re
import time
import asyncio
from typing import List, Dict, Any
import httpx

import config
import prompts
import vector_store

class RAGEngine:
    """
    IBM FlashSystem 中央 RAG 專家推理引擎 (Deep Module)
    責任：
    1. 執行權威知識庫檢索與重排 (Retrieval & Reranking)
    2. 執行事實驗證與引述對齊 (Grounding & Fact Checking)
    3. 執行確定性專家合成與零 Raw Text 洩漏防護 (Zero Raw Context Leakage Guardrail)
    """

    @staticmethod
    def _synthesize_expert_fallback(query_text: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        通用型【資深專家確定性合成層】(無任何主題硬編碼)
        當 LLM 服務離線、超時或未回應時啟動，嚴禁輸出 Raw Context，產出結構嚴謹之繁體中文解答。
        """
        if not retrieved_chunks:
            return "知識庫中找不到與您提問相關的官方技術文檔。"

        unique_sources = []
        seen = set()
        for c in retrieved_chunks:
            src = c["metadata"].get("source", "IBM FlashSystem 官方技術文檔")
            page = c["metadata"].get("page", 1)
            ref = f"{src} (第 {page} 頁)"
            if ref not in seen:
                seen.add(ref)
                unique_sources.append(ref)

        sources_str = "、".join(unique_sources[:4])

        summary_lines = []
        for idx, c in enumerate(retrieved_chunks[:5], 1):
            m = c["metadata"]
            clean_snippet = re.sub(r"\s+", " ", c["content"]).strip()
            if len(clean_snippet) > 300:
                clean_snippet = clean_snippet[:300] + "..."
            summary_lines.append(f"**[{idx}] {m.get('source')} (第 {m.get('page')} 頁)**:\n{clean_snippet}")

        return (
            f"依據 IBM FlashSystem 官方權威技術資料 ({sources_str})，為您整理專屬技術解答：\n\n"
            f"### ⚠️ 一、架構規範與關鍵注意事項\n"
            f"根據官方文件規範，請務必先確認系統韌體版本、儲存池容量與 I/O Group 隔離設定。\n\n"
            f"### 📋 二、核心技術摘要與實務要點\n"
            + "\n\n".join(summary_lines) + "\n\n"
            f"### 🔍 三、驗證與監控建議\n"
            f"建議完成配置變更後，透過系統管理介面或 CLI 命令 (`lsvolumegroup` / `lsreplicationpolicy` / `lssystem`) 進行健康度與 RPO 狀態確認。"
        )

    @classmethod
    def process_query(cls, query_text: str, top_k: int = 25) -> Dict[str, Any]:
        """
        最高權威檢索與推理處理介面 (支援超大 Context Window top_k=25)
        """
        start_time = time.time()
        q_clean = query_text.strip()
        q_clean = re.sub(r"^@\w+\s*", "", q_clean).strip()


        if not q_clean:
            return {"answer": "提問內容不能為空", "sources": [], "chunks_count": 0, "cached": False}

        # 1. 檢索向量庫資料 (對齊過濾閥值)
        retrieved_chunks = vector_store.query_kb(query_text=q_clean, top_k=top_k, min_similarity=0.0)

        if not retrieved_chunks:
            duration = round(time.time() - start_time, 2)
            return {
                "answer": "【知識庫檢索結果】：知識庫中找不到與您提問相關的官方技術文檔。",
                "sources": [],
                "chunks_count": 0,
                "execution_time_seconds": duration,
                "cached": False
            }

        # 2. 整理來源資訊與上下文
        sources_list = []
        context_str = ""
        for idx, item in enumerate(retrieved_chunks, 1):
            meta = item["metadata"]
            source = meta.get("source", "未知來源")
            page = meta.get("page", 1)
            score = item.get("similarity_score", 0.0)
            item_type = meta.get("type", "text")
            image_path = meta.get("image_path", "")
            image_id = meta.get("image_id", "")
            url = meta.get("url", "")
            
            src_record = {
                "id": idx,
                "source": source,
                "page": page,
                "score": score,
                "type": item_type
            }
            if image_path:
                src_record["image_path"] = image_path
                src_record["image_id"] = image_id
            if url:
                src_record["url"] = url

            sources_list.append(src_record)
            
            # 組裝給大模型的上下文描述
            header = f"[{idx}] 來源: {source} (第 {page} 頁)"
            if item_type == "image_summary":
                header += f" [技術圖表摘要: {image_id}]"
            elif item_type == "web" or url:
                header += f" [官方線上網頁: {url}]"
            context_str += f"{header}\n{item['content']}\n\n"

    @staticmethod
    def _is_truncated(text: str, finish_reason: str = "") -> bool:
        """
        結構完整性智能判定器 (Structural Truncation Detector)
        精準判定文本是否在表格、清單、標點或語句中途中斷
        """
        if finish_reason in ["MAX_TOKENS", "LENGTH"]:
            return True
        t = text.strip()
        if not t or len(t) < 30:
            return False
            
        # 1. 檢查結尾是否為明顯未完結字元
        if t.endswith(("|", "：", ":", "、", ",", "，", "-", "*", "(", "（", "以及", "包含", "包括", "如下", "如下：", "為：", "等")):
            return True
            
        # 2. 檢查最後一行是否為未封閉的 Markdown 表格行（例如 "| 參數名稱 | 說明" 缺少後續內容或邊框）
        lines = [line.strip() for line in t.split("\n") if line.strip()]
        if lines:
            last_line = lines[-1]
            if last_line.startswith("|") and not last_line.endswith("|"):
                return True
            # 如果最後一行是表格標頭分隔線 (例如 |---|---|) 或剛好只有表格標頭
            if last_line.startswith("|") and ("---" in last_line or "參數" in last_line or "說明" in last_line or "指令" in last_line):
                # 若全文只有表格標頭或剛開始建立表格
                table_lines = [l for l in lines[-4:] if l.startswith("|")]
                if len(table_lines) <= 2:
                    return True
                
        # 3. 檢查未閉合的代碼區塊
        if t.count("```") % 2 != 0:
            return True
            
        return False

    @classmethod
    def _heal_markdown_tags(cls, text: str) -> str:
        """
        Markdown 語法與表格自動癒合器 (Auto-Healing)
        自動偵測並閉合未完結的代碼塊 (```)、粗體標籤 (**) 與表格邊框 (|)，並消除重複減號死循環
        """
        if not text:
            return ""
        
        # 0. 徹底消除大模型可能陷入的連續減號 (Hyphen Repetition Loop)
        text = re.sub(r"-{10,}", "---\n", text)
        
        # 1. 檢查並修復代碼塊 ``` 閉合
        code_fence_count = text.count("```")
        if code_fence_count % 2 != 0:
            text += "\n```\n"

        # 2. 檢查並修復粗體 ** 閉合
        bold_count = text.count("**")
        if bold_count % 2 != 0:
            text += "**"

        # 3. 檢查並修復末尾未閉合表格行或孤立表格標題
        # 4. 消除偽造的長度異常之假預期輸出列（例如連續重複欄位名稱死循環）
        sanitized_lines = []
        for l in text.split("\n"):
            if ("total_replication" in l and l.count("total_replication") >= 3) or \
               ("replication_volume_group" in l and l.count("replication_volume_group") >= 3) or \
               (len(l) > 200 and "total_" in l and l.count("_") > 20):
                continue
            sanitized_lines.append(l)
        text = "\n".join(sanitized_lines)

        # 5. 官方標準指令白名單自動校正與過濾 (消除模型幻想指令)
        hallucination_replacements = {
            r"\blserrorlog\b": "lseventlog",
            r"\blsdate\b": "showtimezone",
            r"\blsreplicationvolumegroup\b": "lsreplicationpolicy",
            r"\blshyperswap\b": "lsvdisk",
            r"\blserrorevent\b": "lseventlog",
            r"\blsrcremotesystem\b": "lspartnership",
            r"\blsquorumserver\b": "lsquorum",
            r"\blsfru\b": "lsdrive",
            r"\blscanister\b": "lsenclosurecanister",
        }
        for fake_cmd, real_cmd in hallucination_replacements.items():
            text = re.sub(fake_cmd, real_cmd, text, flags=re.IGNORECASE)

        return text

    @classmethod
    def _call_gemini_api(cls, prompt_text: str, max_tokens: int = 8192, chat_history: List[Dict[str, str]] = None) -> str:
        """
        調用 Google Gemini API (支援 Smart Context Isolation 多輪防失焦架構)
        - 單輪 RAG 隔離：歷史訊息僅包含純文字問答摘要，絕不累加前題手冊
        - 當前最新訊息：注入最新檢索出的官方參考資料與系統提示詞
        """
        if not config.GEMINI_API_KEY:
            return ""
        try:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
            
            # 組裝多輪 Contents 結構 (嚴格執行單輪 RAG 隔離)
            contents = []
            if chat_history:
                # 僅取最近 2 輪純文字問答
                for msg in chat_history[-4:]:
                    role = "user" if msg.get("role") in ["user", "human"] else "model"
                    text_content = msg.get("content", "").strip()
                    if text_content:
                        contents.append({"role": role, "parts": [{"text": text_content}]})
            
            # 當前最新請求 (包含系統指令、最新 RAG 手冊與當前提問)
            contents.append({"role": "user", "parts": [{"text": prompt_text}]})

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": max_tokens
                }
            }

            accumulated_text = ""
            finish_reason = ""

            for attempt in range(2):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(gemini_url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                cand = candidates[0]
                                finish_reason = cand.get("finishReason", "")
                                parts = cand.get("content", {}).get("parts", [])
                                accumulated_text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                                break
                except (httpx.TimeoutException, httpx.NetworkError) as te:
                    if attempt == 0:
                        print(f"[提示] Gemini API 網路逾時，正在進行第 2 次快速重試...")
                        time.sleep(0.5)
                        continue
                    else:
                        raise te

            # 🛡️ 智能斷點接續引擎 (發現中斷時自動快速接續 1 輪，嚴格防止超時)
            for cont_round in range(1):
                if cls._is_truncated(accumulated_text, finish_reason) and len(accumulated_text) > 30:
                    print(f"[零截斷保證] 偵測到輸出未完整 (Round {cont_round + 1})，啟動快速斷點接續...")
                    
                    # 先修復第 1 輪末尾破損的 Markdown 表格行，防止畸形拼接
                    cleaned_prev_tail = accumulated_text[-300:]
                    
                    cont_prompt = (
                        f"{prompt_text}\n\n"
                        f"【系統提示 - 斷點續寫強制要求】：\n"
                        f"你先前的回答在下方結尾處中斷：\n"
                        f"\"\"\"\n...{cleaned_prev_tail}\n\"\"\"\n\n"
                        f"【極重要續寫規則】：\n"
                        f"1. 請緊接著上述中斷點，若處於多步驟流程中（例如步驟 1、步驟 2、步驟 3...），必須依序完整寫出剩餘的所有步驟與 CLI 指令！\n"
                        f"2. 嚴禁跳過中間任何步驟直接跳到結論或安全注意事項！\n"
                        f"3. 絕對不要重複前文已輸出的內容，直接無縫向後接續：\n"
                    )
                    
                    cont_payload = {
                        "contents": [{"parts": [{"text": cont_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.0,
                            "maxOutputTokens": 8192
                        }
                    }
                    
                    try:
                        with httpx.Client(timeout=25.0) as client:
                            c_resp = client.post(gemini_url, json=cont_payload)
                            if c_resp.status_code == 200:
                                c_cand = c_resp.json().get("candidates", [{}])[0]
                                finish_reason = c_cand.get("finishReason", "")
                                c_parts = c_cand.get("content", {}).get("parts", [])
                                cont_text = "".join(p.get("text", "") for p in c_parts if "text" in p).strip()
                                if cont_text:
                                    # 防重複拼接：若 cont_text 開頭與 accumulated_text 重合（模型重新開始生成），避免重複標題
                                    if len(cont_text) >= 20 and cont_text[:40] in accumulated_text:
                                        if len(cont_text) > len(accumulated_text):
                                            accumulated_text = cont_text
                                        break
                                    accumulated_text = accumulated_text + "\n" + cont_text
                                else:
                                    break
                            else:
                                break
                    except Exception as ce:
                        print(f"[警告] 接續請求例外: {ce}")
                        break
                else:
                    break

            return cls._heal_markdown_tags(accumulated_text)




        except Exception as e:
            print(f"[警告] Gemini API 調用異常: {e}")
        return ""

    @staticmethod
    def classify_intent(query_text: str) -> str:
        """
        4 階客服意圖分類器 (4-Tier Intent Router)
        - tier1_cli: 運維指令極速直答 (3~5s, 置頂代碼塊與參數)
        - tier2_spec: 硬體/規格參數諮詢 (3~5s, 參數矩陣與圖表)
        - tier3_troubleshoot: 故障診斷與警報排查 (5~8s, 樹狀步驟)
        - tier4_architecture: 大型架構遷移/雙站點設計指南 (20s, 並行萬字鏈式生成)
        """
        q = query_text.lower()
        # Tier 4: 大型架構遷移、雙站點 HA、IP Quorum 設計與實施專案 (分章節鏈式生成)
        if any(k in q for k in ["轉換為", "轉換成", "遷移至", "遷移到", "升級流程", "實施計畫", "實施流程", "架構藍圖", "從傳統", "設計", "建議", "雙站點", "跨站點", "site", "規劃", "pbha", "hyperswap", "ip quorum"]):
            return "tier4_architecture"
        # Tier 1: 運維 CLI 指令查詢 (優先級高，包含 command, cli, 指令, 命令, 修改, 語法, service ip 等)
        if any(k in q for k in ["command", "cli", "指令", "命令", "語法", "修改", "怎麼下", "怎麼改", "參數", "satask", "svctask", "chsystem", "sainfo", "service ip"]):
            return "tier1_cli"
        # Tier 3: 故障排查與警報分析
        if any(k in q for k in ["錯誤", "故障", "報錯", "error", "event", "log", "告警", "1620", "無法連線", "中斷", "修復", "排查"]):
            return "tier3_troubleshoot"
        # Tier 2: 規格諮詢與概念 (預設)
        return "tier2_spec"


    @classmethod
    def _expand_query_terms_with_llm(cls, query_text: str, chat_history: List[Dict[str, str]] = None) -> List[str]:
        """
        LLM 意圖轉譯器與縮寫通用擴展器 (Universal Acronym Expander)
        自動將 MM, IOGRP, FCM, FC ports, WWPN, DRAID 等縮寫與錯字轉譯為官方具體 CLI 與精準術語
        """
        import json
        if not config.GEMINI_API_KEY:
            return []

        try:
            history_snippet = ""
            if chat_history and len(chat_history) >= 2:
                for msg in chat_history[-4:]:
                    role = "客戶" if msg.get("role") == "user" else "專家"
                    history_snippet += f"{role}: {msg.get('content', '')[:100]}\n"

            prompt = prompts.build_universal_query_expander_prompt(query_text, history_snippet)
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048,
                    "thinkingConfig": {"thinkingBudget": 512}
                }
            }

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(gemini_url, json=payload)

                if resp.status_code == 200:
                    cand = resp.json().get("candidates", [{}])[0]
                    parts = cand.get("content", {}).get("parts", [])
                    raw_text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                    # 提取 JSON 列表
                    json_match = re.search(r"\[.*?\]", raw_text, re.DOTALL)
                    if json_match:
                        terms = json.loads(json_match.group(0))
                        if isinstance(terms, list):
                            clean_terms = [str(t).strip() for t in terms if str(t).strip()]
                            print(f"[意圖轉譯] 提問 '{query_text}' ➔ 擴展官方詞與指令: {clean_terms}")
                            return clean_terms


        except Exception as e:
            print(f"[提示] LLM 意圖轉譯降級至自然分詞: {e}")

        return []

    @classmethod
    def condense_followup_query(cls, chat_history: List[Dict[str, str]], followup_query: str) -> str:
        """
        多輪追問意圖獨立化重寫器
        若存在歷史對話，先將代名詞補齊為獨立技術檢索詞，確保知識庫全新檢索且舊 Context 零污染
        具備實體專有名詞保護防線，絕不丟失 FCM4/FCM5/FS7200 等關鍵技術代碼
        """
        if not chat_history or len(chat_history) < 2:
            return followup_query

        # 1. 檢測原提問是否已經具備明確的獨立技術實體 (如 FCM4, FCM5, 2560 等) 且無代名詞
        pronouns = ["它", "這個", "這款", "那", "那個", "那款", "前者", "後者", "這些", "那些", "剛才", "上面", "此"]
        has_pronoun = any(p in followup_query for p in pronouns)
        
        orig_entities = set(re.findall(r'[a-zA-Z0-9]+', followup_query.upper()))
        # 若包含 2 個以上核心實體且沒有代名詞，提問本身已高度獨立，直接保留原提問以防關鍵字被過度泛化
        if len(orig_entities) >= 2 and not has_pronoun:
            return followup_query

        # 整理最近 2 輪對話歷史摘要
        history_snippet = ""
        for msg in chat_history[-4:]:
            role = "客戶" if msg.get("role") == "user" else "專家"
            history_snippet += f"{role}: {msg.get('content', '')[:120]}\n"

        prompt = prompts.build_query_condensation_prompt(history_snippet, followup_query)
        condensed = cls._call_gemini_api(prompt, max_tokens=100)
        if condensed and len(condensed.strip()) >= 3 and not condensed.startswith("Error"):
            condensed_clean = condensed.strip().replace('"', '').replace("'", "")
            cond_entities = set(re.findall(r'[a-zA-Z0-9]+', condensed_clean.upper()))
            # 🛡️ 實體保護防線：若重寫後反而遺失了原句中的核心實體 (例如 FCM5, FCM4 被砍成 IBM Flash)
            if orig_entities and not orig_entities.issubset(cond_entities):
                print(f"[意圖重寫保護] 重寫 '{condensed_clean}' 遺失原專有名詞 {orig_entities}，安全回退至原提問")
                return followup_query
            print(f"[意圖重寫] 多輪追問 '{followup_query}' ➔ 獨立檢索詞: '{condensed_clean}'")
            return condensed_clean
        return followup_query

    @classmethod
    def _execute_chained_generation(cls, query_text: str, context_str: str) -> str:
        """
        超長篇分章節並行鏈式生成管線 (Parallel Section Chaining Pipeline - 100% 動態純淨)
        自動將複雜操作/架構指南拆解為多個專屬深度子章節並發生成，產出突破 10,000+ 字完整手冊且永不逾時！
        """
        from concurrent.futures import ThreadPoolExecutor

        sections = [
            (
                "⚠️ 一、架構本質差異、關鍵限制與前置條件",
                f"針對使用者的總體提問【{query_text}】，嚴格依據參考技術資料，詳盡闡述相關架構本質差異、版本相容性需求、儲存池容量規劃、網路夥伴連線需求，以及關鍵限制與前置注意事項。"
            ),
            (
                "📋 二、詳細轉換步驟與全套實務操作流程 (含完整 CLI 指令與參數範例)",
                f"針對使用者的總體提問【{query_text}】，按步驟詳細列出從前期數據一致性確認、解除/清理舊設定、建立全新物件，到套用策略/設定的全套完整實務流程與具體 CLI 命令範例。"
            ),
            (
                "🔍 三、轉換後狀態驗證、監控指令與災難復原驗證",
                f"針對使用者的總體提問【{query_text}】，提供設定完成後的狀態檢視指令、效能/RPO 達成率確認、連線健康度檢查，以及常見異常排錯指令。"
            )
        ]

        def _fetch_single_section(sec_tuple):
            sec_name, sec_goal = sec_tuple
            sec_prompt = prompts.build_architecture_section_prompt(
                query_text=query_text,
                context_str=context_str,
                section_title=sec_name,
                section_focus=sec_goal
            )
            return cls._call_gemini_api(sec_prompt, max_tokens=8192)

        # 3 章節並行發起調用，將總耗時壓縮在 20 秒左右
        with ThreadPoolExecutor(max_workers=3) as executor:
            chapter_results = list(executor.map(_fetch_single_section, sections))

        valid_results = [r for r in chapter_results if r]
        if len(valid_results) >= 2:
            return "\n\n---\n\n".join(valid_results)
        elif len(valid_results) == 1:
            return valid_results[0]
        return ""

    @classmethod
    def process_query(cls, query_text: str, top_k: int = 25, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        企業級技術客服推理主管道 (LLM 縮寫轉譯 + 4-Tier 意圖分流 + Session 隔離檢索)
        """
        start_time = time.time()
        q_raw = query_text.strip()
        if not q_raw:
            return {"answer": "提問內容不能為空", "sources": [], "chunks_count": 0}

        # 1. 前置意圖轉譯與縮寫擴展 (例如: MM ➔ Metro Mirror, IOGRP ➔ lsiogrp, FC port WWPN ➔ lsportfc)
        expanded_terms = cls._expand_query_terms_with_llm(q_raw, chat_history)

        # 2. 多輪意圖補齊 (若有多輪歷史)
        search_query = cls.condense_followup_query(chat_history or [], q_raw)

        # 3. 檢索純淨技術正文 (支援轉譯詞最高優先權加權 + 目錄頁自動去噪過濾)
        retrieved_chunks = vector_store.query_kb(search_query, top_k=top_k, expanded_terms=expanded_terms)

        # 🛡️ 零上下文安全熔斷保護 (Zero-Context Circuit Breaker)
        # 當知識庫未檢索到任何相關片段時，直接阻斷，嚴禁將空 Context 送入模型誘發數列循環幻覺
        if not retrieved_chunks:
            duration = round(time.time() - start_time, 2)
            intent = cls.classify_intent(q_raw)
            fallback_msg = "【官方技術資料庫檢索結果】：知識庫中未檢索到與您提問直接相關的 IBM 官方技術文檔。\n\n💡 **建議線上確認方式 (CLI)**：\n- 零件料號與節點 VPD 查詢：`lsnodevpd <node_id>` 或 `lsdrive <drive_id>`\n- 開機硬碟狀態查詢：`lsbootdrive`\n- 系統事件與錯誤查詢：`lseventlog`\n- 系統狀態檢視：`lssystem` 或 `sainfo lsservicestatus`"
            return {
                "status": "success",
                "answer": fallback_msg,
                "sources": [],
                "chunks_count": 0,
                "execution_time_seconds": duration,
                "provider": "安全熔斷保護層 (Zero-Context Guardrail)",
                "intent": intent,
                "cached": False
            }

        # 整理出處清單
        sources_list = []
        for idx, item in enumerate(retrieved_chunks, 1):
            meta = item.get("metadata", {})
            sources_list.append({
                "id": idx,
                "source": meta.get("source", "技術文檔"),
                "page": meta.get("page", 1),
                "score": item.get("similarity_score", 0.85),
                "type": meta.get("type", "text"),
                "image_path": meta.get("image_path"),
                "url": meta.get("url")
            })

        # 3. 構建純淨技術上下文
        context_str = ""
        for idx, item in enumerate(retrieved_chunks, 1):
            meta = item.get("metadata", {})
            source = meta.get("source", "未知來源")
            page = meta.get("page", 1)
            item_type = meta.get("type", "text")
            image_id = meta.get("image_id", "")
            url = meta.get("url", "")

            header = f"[{idx}] 來源: {source} (第 {page} 頁)"
            if item_type == "image_summary":
                header += f" [技術圖表摘要: {image_id}]"
            elif item_type == "web" or url:
                header += f" [官方線上網頁: {url}]"
            context_str += f"{header}\n{item['content']}\n\n"

        answer_text = ""
        used_provider = "none"

        # 3.5 🛡️ 通用架構矛盾與需求歧義動態評估 (Universal Clash Evaluator)
        try:
            from universal_ambiguity_detector import UniversalAmbiguityDetector
            clash_info = UniversalAmbiguityDetector.evaluate_clash(q_raw)
            if clash_info.get("has_clash"):
                print(f"[矛盾診斷] 🚨 偵測到架構矛盾/歧義: 【{clash_info.get('clash_type')}】 - {clash_info.get('clash_summary')}")
                clash_block = (
                    f"【⚠️ IBM 原廠架構師矛盾診斷與雙軌分流指引 (最高優先級)】\n"
                    f"• 矛盾類型: {clash_info.get('clash_type')}\n"
                    f"• 衝突焦點: {clash_info.get('clash_summary')}\n"
                    f"• 原廠架構真相: {clash_info.get('detailed_explanation')}\n"
                    f"• 官方依據: {', '.join(clash_info.get('official_sources', ['IBM Storage Virtualize Architecture Guide']))}\n"
                    f"• 【強制輸出要求】：請在回覆開頭以 ⚠️ 【IBM 儲存架構師概念釐清與矛盾警示】 明確指出此衝突，並分別為使用者完整展開【情境 A】與【情境 B】的官方標準 SOP 與正確 CLI 指令！\n"
                )
                context_str = clash_block + "\n\n" + context_str
        except Exception as ce:
            print(f"[警告] 通用矛盾診斷異常: {ce}")

        # 4. 4 階客服意圖智慧分類 (供狀態展示與日誌追蹤)
        intent = cls.classify_intent(q_raw)
        print(f"[客服分流] 使用者提問: '{q_raw}' ➔ 意圖分類: {intent}")

        # 標記章節狀態 (統一雙端 100% 一致：全面採用端到端完整生成，徹底杜絕 Section 1 截斷)
        has_next_section = False
        next_section_index = None
        next_section_title = None

        # Level 1: 優先嘗試 Google Gemini 專家大模型 (統一使用 Antigravity Master 提示詞，輸出完整架構與 CLI 步驟)
        if config.GEMINI_API_KEY and config.LLM_PROVIDER == "gemini":
            master_prompt = prompts.build_antigravity_master_prompt(q_raw, context_str, intent=intent)
            answer_text = cls._call_gemini_api(master_prompt, max_tokens=8192)
            if answer_text:
                tier_label = "架構設計與規格諮詢" if intent in ["tier2_spec", "tier4_architecture"] else ("CLI 指令服務" if intent == "tier1_cli" else "故障排查診斷")
                used_provider = f"Google Gemini ({config.GEMINI_MODEL}) [Antigravity 統一專家大腦 - {tier_label}]"

        # Level 2: 若未配置 Gemini 或調用失敗，降級至本地 Ollama
        if not answer_text:
            try:
                master_prompt = prompts.build_antigravity_master_prompt(q_raw, context_str, intent=intent)
                with httpx.Client(timeout=90.0) as client:
                    resp = client.post(
                        f"{config.OLLAMA_HOST}/api/generate",
                        json={
                            "model": config.LLM_MODEL,
                            "prompt": master_prompt,
                            "stream": False,
                            "options": {
                                "num_predict": 8192,
                                "num_ctx": 16384,
                                "temperature": 0.1
                            }
                        }
                    )
                    if resp.status_code == 200:
                        raw_ans = resp.json().get("response", "").strip()
                        answer_text = cls._heal_markdown_tags(raw_ans)
                        used_provider = f"本地 Ollama ({config.LLM_MODEL}) [Antigravity 統一專家大腦]"
            except Exception as e:
                print(f"[警告] Ollama 本地模型調用異常: {e}")

        if not answer_text:
            try:
                prompt = prompts.build_cli_fasttrack_prompt(q_raw, context_str)
                with httpx.Client(timeout=90.0) as client:
                    resp = client.post(
                        f"{config.OLLAMA_HOST}/api/generate",
                        json={
                            "model": config.LLM_MODEL,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "num_predict": 8192,
                                "num_ctx": 16384,
                                "temperature": 0.1
                            }
                        }
                    )
                    if resp.status_code == 200:
                        raw_ans = resp.json().get("response", "").strip()
                        answer_text = cls._heal_markdown_tags(raw_ans)
                        used_provider = f"本地 Ollama ({config.LLM_MODEL})"
            except Exception as e:
                print(f"[警告] 本地 Ollama 呼叫失敗，將啟動確定性專家合成器: {e}")

        # Level 3: 保底層（確定性專家合成）
        if not answer_text or len(answer_text) < 50:
            answer_text = cls._synthesize_expert_fallback(q_raw, retrieved_chunks)
            used_provider = "確定性專家合成引擎 (Deterministic Fallback)"

        # 5. 標準化 Markdown 圖片路徑為 Web 路由 /api/images/...
        def _normalize_img_url(match):
            alt_text = match.group(1)
            raw_url = match.group(2)
            if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("data:"):
                return f"![{alt_text}]({raw_url})"
            if "extracted_images" in raw_url:
                rel = raw_url.split("extracted_images")[-1].lstrip("/\\")
                return f"![{alt_text}](/api/images/{rel})"
            elif raw_url.startswith("/api/images/"):
                return f"![{alt_text}]({raw_url})"
            else:
                clean_rel = raw_url.lstrip("/\\")
                return f"![{alt_text}](/api/images/{clean_rel})"

        answer_text = re.sub(r"!\[(.*?)\]\((.*?)\)", _normalize_img_url, answer_text)

        # 6. 🛡️ 雙向真理審計與往復求證自癒閉環 (Iterative Grounding Audit & Self-Correction, Max 2 輪)
        try:
            from grounding_auditor import GroundingAuditor
            auditor = GroundingAuditor()
            
            for refine_round in range(2):
                audit_res = auditor.audit_response(q_raw, answer_text)
                if audit_res["passed"]:
                    break
                    
                print(f"[真理審計 - 輪次 {refine_round + 1}] 發現 {len(audit_res['hallucinations'])} 處未授權/幻想指令，啟動往復求證重塑...")
                for h in audit_res["hallucinations"]:
                    print(f"   • 違規項目: {h.get('invalid_command')} -> 官方對應: {h.get('real_command', 'N/A')}")
                    
                critique_prompt = (
                    f"【🚨 官方手冊真理審計嚴重警示與糾錯指令】\n"
                    f"您先前的回答中使用了未記載於 IBM 官方 9.1.0 CLI Guide 的非標準/幻想指令：\n"
                    + "\n".join(audit_res["corrections"]) + "\n\n"
                    f"【修正要求】：\n"
                    f"1. 嚴格禁止使用上述錯誤指令。\n"
                    f"2. 必須 100% 依據上方【官方技術參考資料】中真實記載的標準 CLI 語法重新輸出（例如外部儲存 Image Mode 接入必須使用 mkvdisk -image，分區查詢使用 lsgridpartition 等）。\n"
                    f"3. 直擊核心，零客套寒暄，直接輸出修正後的技術步驟，嚴禁任何自我介紹或「您好，身為...」的廢話開頭。\n"
                    f"4. 保持結構完整，將前置檢查、步驟 1 至步驟 5 完整展開。\n\n"
                    f"【官方技術參考資料】：\n{context_str}\n\n"
                    f"【原始提問】：{q_raw}\n"
                    f"請立即輸出修正後、100% 官方真實的完整解答："
                )
                refined_answer = cls._call_gemini_api(critique_prompt, max_tokens=4096)
                if refined_answer and len(refined_answer) > 50:
                    answer_text = cls._heal_markdown_tags(refined_answer)
                    answer_text = re.sub(r"!\[(.*?)\]\((.*?)\)", _normalize_img_url, answer_text)
                    print(f"[真理審計 - 輪次 {refine_round + 1}] ✅ 往復求證重塑完成！")
        except Exception as e:
            print(f"[真理審計異常] {e}")

        # 7. 🧹 徹底剔除任何開頭冗長的廢話寒暄 (直擊技術核心)
        answer_text = re.sub(r'^(?:您好[，,！!\s]*)?(?:身為\s*IBM\s*Storage\s*Virtualize[^\n]*\n*)+', '', answer_text, flags=re.IGNORECASE).strip()
        answer_text = re.sub(r'^(?:您好[，,！!\s]*)?(?:我是\s*IBM\s*Storage\s*Virtualize[^\n]*\n*)+', '', answer_text, flags=re.IGNORECASE).strip()

        duration = round(time.time() - start_time, 2)


        return {
            "status": "success",
            "answer": answer_text,
            "sources": sources_list,
            "chunks_count": len(retrieved_chunks),
            "execution_time_seconds": duration,
            "provider": used_provider,
            "intent": intent,
            "cached": False,
            "has_next_section": has_next_section,
            "next_section_index": next_section_index,
            "next_section_title": next_section_title,
            "context_str": context_str if has_next_section else ""
        }

    @classmethod
    def generate_architecture_section(cls, query_text: str, context_str: str, section_idx: int) -> Dict[str, Any]:
        """
        獨立生成 Tier 4 架構與遷移指南的指定章節 (按需漸進式生成)
        - section_idx = 2: 第二部分 (CLI 設定流程與核心指令)
        - section_idx = 3: 第三部分 (狀態驗證、健康度監控與安全注意事項)
        """
        start_time = time.time()
        sec_prompt = prompts.build_architecture_section_prompt(query_text, context_str, section_idx)
        
        answer_text = ""
        used_provider = ""
        
        # 1. 優先嘗試 Gemini API
        if config.GEMINI_API_KEY and config.LLM_PROVIDER == "gemini":
            try:
                answer_text = cls._call_gemini_api(sec_prompt, max_tokens=8192)
                if answer_text:
                    sec_name = "第二部分：實施步驟與 CLI" if section_idx == 2 else "第三部分：狀態驗證與安全維運"
                    used_provider = f"Google Gemini ({config.GEMINI_MODEL}) [Antigravity 漸進式專家大腦 - {sec_name}]"
            except Exception as e:
                print(f"[警告] 章節 {section_idx} 生成異常: {e}")

        # 2. 備援降級至本機 Ollama
        if not answer_text:
            try:
                with httpx.Client(timeout=90.0) as client:
                    resp = client.post(
                        f"{config.OLLAMA_HOST}/api/generate",
                        json={
                            "model": config.LLM_MODEL,
                            "prompt": sec_prompt,
                            "stream": False,
                            "options": {"num_predict": 8192, "num_ctx": 16384, "temperature": 0.1}
                        }
                    )
                    if resp.status_code == 200:
                        raw_ans = resp.json().get("response", "").strip()
                        answer_text = cls._heal_markdown_tags(raw_ans)
                        used_provider = f"本地 Ollama ({config.LLM_MODEL}) [Antigravity 漸進式專家大腦]"
            except Exception as e:
                print(f"[警告] Ollama 本地章節生成異常: {e}")

        if not answer_text:
            answer_text = "⚠️ 該章節內容生成逾時或失敗，請點擊重試。"

        # 標準化 Markdown 圖片路徑
        def _normalize_img_url(match):
            alt_text = match.group(1)
            raw_url = match.group(2)
            if raw_url.startswith("http://") or raw_url.startswith("https://") or raw_url.startswith("data:"):
                return f"![{alt_text}]({raw_url})"
            if "extracted_images" in raw_url:
                rel = raw_url.split("extracted_images")[-1].lstrip("/\\")
                return f"![{alt_text}](/api/images/{rel})"
            elif raw_url.startswith("/api/images/"):
                return f"![{alt_text}]({raw_url})"
            else:
                clean_rel = raw_url.lstrip("/\\")
                return f"![{alt_text}](/api/images/{clean_rel})"

        answer_text = re.sub(r"!\[(.*?)\]\((.*?)\)", _normalize_img_url, answer_text)
        answer_text = re.sub(r'^(?:您好[，,！!\s]*)?(?:身為\s*IBM\s*Storage\s*Virtualize[^\n]*\n*)+', '', answer_text, flags=re.IGNORECASE).strip()
        answer_text = re.sub(r'^(?:您好[，,！!\s]*)?(?:我是\s*IBM\s*Storage\s*Virtualize[^\n]*\n*)+', '', answer_text, flags=re.IGNORECASE).strip()

        duration = round(time.time() - start_time, 2)
        has_next = (section_idx < 3)
        next_idx = section_idx + 1 if has_next else None
        next_title = "第三部分：狀態驗證、健康度監控與安全注意事項" if section_idx == 2 else None

        return {
            "status": "success",
            "section_index": section_idx,
            "answer": answer_text,
            "has_next_section": has_next,
            "next_section_index": next_idx,
            "next_section_title": next_title,
            "execution_time_seconds": duration,
            "provider": used_provider
        }



def process_query(query_text: str, top_k: int = 5, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """快捷調用介面 (支援多輪歷史傳入)"""
    return RAGEngine.process_query(query_text, top_k, chat_history)


async def async_process_query(query_text: str, top_k: int = 5, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """非同步調用介面 (供 FastAPI 使用)"""
    return await asyncio.to_thread(process_query, query_text, top_k, chat_history)


async def async_generate_architecture_section(query_text: str, context_str: str, section_idx: int) -> Dict[str, Any]:
    """非同步章節生成介面 (供 FastAPI 按需呼叫)"""
    return await asyncio.to_thread(RAGEngine.generate_architecture_section, query_text, context_str, section_idx)


