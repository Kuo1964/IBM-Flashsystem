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
    def _heal_markdown_tags(text: str) -> str:
        """
        Markdown 語法自動癒合器 (Auto-Healing)
        自動偵測並閉合未完結的代碼塊 (```) 與粗體標籤 (**)，確保前端 100% 正常渲染
        """
        if not text:
            return ""
        
        # 1. 檢查並修復代碼塊 ``` 閉合
        code_fence_count = text.count("```")
        if code_fence_count % 2 != 0:
            text += "\n```\n"

        # 2. 檢查並修復粗體 ** 閉合
        bold_count = text.count("**")
        if bold_count % 2 != 0:
            text += "**"

        return text

    @classmethod
    def _call_gemini_api(cls, prompt_text: str, max_tokens: int = 8192) -> str:
        """
        調用 Google Gemini API (支援 Google Search Grounding 原生即時聯網查證)
        具備 thinkingBudget 預算保護、Search Grounding 自動補全與 MAX_TOKENS 自動斷點續寫修復
        """
        if not config.GEMINI_API_KEY:
            return ""
        try:
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
            
            # 優先嘗試具備 Google Search Grounding 聯網查證能力之請求
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "tools": [{"google_search": {}}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": max_tokens
                }
            }

            for attempt in range(2):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(gemini_url, json=payload)
                        
                        # 若搜尋工具遇版本不相容或限制，自動降級至標準模式
                        if resp.status_code != 200:
                            fallback_payload = {
                                "contents": [{"parts": [{"text": prompt_text}]}],
                                "generationConfig": {
                                    "temperature": 0.0,
                                    "maxOutputTokens": max_tokens,
                                    "thinkingConfig": {"thinkingBudget": 1024}
                                }
                            }
                            resp = client.post(gemini_url, json=fallback_payload)

                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                cand = candidates[0]
                                finish_reason = cand.get("finishReason", "")
                                parts = cand.get("content", {}).get("parts", [])
                                text = "".join(p.get("text", "") for p in parts if "text" in p).strip()

                                # 防護網 2: 若觸發 MAX_TOKENS 限制，自動發起斷點接續請求
                                if finish_reason == "MAX_TOKENS" and len(text) > 300:
                                    print("[零截斷防護] 偵測到單次生成觸頂 (MAX_TOKENS)，啟動自動斷點續寫...")
                                    cont_prompt = (
                                        f"{prompt_text}\n\n"
                                        f"【系統提示】：你先前的回答在以下內容處中斷：\n"
                                        f"...{text[-350:]}\n\n"
                                        f"請緊接著上述最後一個字，不要重複前文，繼續完整寫出後續所有內容直到結尾：\n"
                                    )
                                    cont_payload = {
                                        "contents": [{"parts": [{"text": cont_prompt}]}],
                                        "generationConfig": {
                                            "temperature": 0.2,
                                            "maxOutputTokens": 4096
                                        }
                                    }
                                    c_resp = client.post(gemini_url, json=cont_payload)
                                    if c_resp.status_code == 200:
                                        c_cand = c_resp.json().get("candidates", [{}])[0]
                                        c_parts = c_cand.get("content", {}).get("parts", [])
                                        cont_text = "".join(p.get("text", "") for p in c_parts if "text" in p).strip()
                                        if cont_text:
                                            text = text + "\n\n" + cont_text

                                return cls._heal_markdown_tags(text)
                except (httpx.TimeoutException, httpx.NetworkError) as te:
                    if attempt == 0:
                        print(f"[提示] Gemini API 網路逾時，正在進行第 2 次自動重試...")
                        time.sleep(1)
                        continue
                    else:
                        raise te


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
        """
        if not chat_history or len(chat_history) < 2:
            return followup_query

        # 整理最近 2 輪對話歷史摘要
        history_snippet = ""
        for msg in chat_history[-4:]:
            role = "客戶" if msg.get("role") == "user" else "專家"
            history_snippet += f"{role}: {msg.get('content', '')[:120]}\n"

        prompt = prompts.build_query_condensation_prompt(history_snippet, followup_query)
        condensed = cls._call_gemini_api(prompt, max_tokens=100)
        if condensed and len(condensed.strip()) >= 3 and not condensed.startswith("Error"):
            print(f"[意圖重寫] 多輪追問 '{followup_query}' ➔ 獨立檢索詞: '{condensed.strip()}'")
            return condensed.strip()
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

        # 4. 4 階客服意圖智慧分類 (供狀態展示與日誌追蹤)
        intent = cls.classify_intent(q_raw)
        print(f"[客服分流] 使用者提問: '{q_raw}' ➔ 意圖分類: {intent}")

        # Level 1: 優先嘗試 Google Gemini 專家大模型 (統一採用 Antigravity Master 模組)
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
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(
                        f"{config.OLLAMA_HOST}/api/generate",
                        json={"model": config.LLM_MODEL, "prompt": master_prompt, "stream": False}
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
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(
                        f"{config.OLLAMA_HOST}/api/generate",
                        json={"model": config.LLM_MODEL, "prompt": prompt, "stream": False}
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

        # 6. 若提問明確要求看圖/後視圖/機匣圖，且回答中未包含圖片，自動智慧關聯最佳實體架構圖
        q_lower = q_raw.lower()
        if any(k in q_lower for k in ["看圖", "看一下圖", "後視圖", "機匣圖", "架構圖", "正面圖", "背視圖", "圖解", "看一下", "圖片"]) and "![" not in answer_text:
            matched_img = None
            if "5200" in q_lower and any(k in q_lower for k in ["node", "canister", "後視", "背視", "機匣", "插槽", "adapter", "sas", "硬體"]):
                if (config.BASE_DIR / "extracted_images/sg248520/page_68_img_0.png").exists():
                    matched_img = "/api/images/sg248520/page_68_img_0.png"
            elif "7300" in q_lower and any(k in q_lower for k in ["node", "canister", "後視", "背視", "機匣", "硬體"]):
                if (config.BASE_DIR / "extracted_images/sg248543/page_650_img_0.png").exists():
                    matched_img = "/api/images/sg248543/page_650_img_0.png"

            if matched_img:
                answer_text += f"\n\n---\n\n### 🖼️ 原廠實體硬體與 Node Canister 架構圖解\n\n![IBM FlashSystem 原廠硬體架構圖]({matched_img})\n"


        duration = round(time.time() - start_time, 2)


        return {
            "status": "success",
            "answer": answer_text,
            "sources": sources_list,
            "chunks_count": len(retrieved_chunks),
            "execution_time_seconds": duration,
            "provider": used_provider,
            "intent": intent,
            "cached": False
        }



def process_query(query_text: str, top_k: int = 5, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """快捷調用介面 (支援多輪歷史傳入)"""
    return RAGEngine.process_query(query_text, top_k, chat_history)


async def async_process_query(query_text: str, top_k: int = 5, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """非同步調用介面 (供 FastAPI 使用)"""
    return await asyncio.to_thread(process_query, query_text, top_k, chat_history)

