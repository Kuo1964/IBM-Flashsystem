import chromadb
import config
import json
from typing import List, Dict, Any, Optional
import httpx
import uuid

class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    """自訂 ChromaDB 使用的 Ollama Embedding 介面"""
    def __init__(self, model_name: str = config.EMBEDDING_MODEL, host: str = config.OLLAMA_HOST):
        self.model_name = model_name
        self.host = host

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            response = httpx.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
                timeout=120.0
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        return embeddings

from chromadb.config import Settings

_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None

def get_chroma_collection():
    """取得或建立 ChromaDB 集合 (安全單例模式，徹底杜絕重複建立 Client 誘發 C++ HNSW 記憶體崩潰與佇列衝突)"""
    global _CHROMA_CLIENT, _CHROMA_COLLECTION
    if _CHROMA_COLLECTION is not None:
        return _CHROMA_COLLECTION

    if _CHROMA_CLIENT is None:
        _CHROMA_CLIENT = chromadb.PersistentClient(
            path=str(config.VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False, allow_reset=False)
        )

    embedding_fn = OllamaEmbeddingFunction()
    _CHROMA_COLLECTION = _CHROMA_CLIENT.get_or_create_collection(
        name="ibm_flashsystem_kb",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return _CHROMA_COLLECTION

def add_chunks_to_db(chunks: List[Dict[str, Any]]):
    """將文字 Chunk 寫入知識庫 (正統 ChromaDB API)"""
    if not chunks:
        return
        
    collection = get_chroma_collection()
    
    ids = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        cid = str(chunk.get("id") or chunk.get("chunk_id") or uuid.uuid4())
        text = str(chunk.get("content") or chunk.get("text") or "")
        meta = chunk.get("metadata", {})
        
        if not text:
            continue
            
        ids.append(cid)
        documents.append(text)
        metadatas.append(meta)
        
    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"  [成功] 已將 {len(ids)} 筆記錄寫入 ChromaDB，包含完整向量與來源。")

def delete_source_from_db(source_name: str):
    """安全清除指定來源資料"""
    collection = get_chroma_collection()
    collection.delete(where={"source": source_name})
    print(f"  [資訊] 已清除來源 '{source_name}' 之舊記錄。")

def is_pure_toc_chunk(text: str) -> bool:
    """判斷是否為純目錄導覽/超連結列表 Chunk (過濾無意義的 TOC 噪聲)"""
    if not text:
        return False
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 3:
        return False
    link_lines = [l for l in lines if l.startswith('- [') or l.startswith('* [') or ('](/docs/' in l and len(l) < 120)]
    dot_lines = [l for l in lines if '....' in l or '····' in l or '   . ' in l]
    if (len(link_lines) / len(lines)) >= 0.4 or (len(dot_lines) / len(lines)) >= 0.3:
        return True
    return False

def lexical_search_kb(query_text: str, expanded_terms: List[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    透過 SQLite 全文關鍵字精準匹配 (Exact Lexical & Token Search)
    專門解決數字、料號 (Part Numbers / FRU)、Feature Codes、硬體零件代碼在密集向量中語意稀釋的問題
    """
    import sqlite3
    import re
    
    db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
    if not db_path.exists():
        db_path = config.BASE_DIR / "vector_db" / "chroma.sqlite3"
    if not db_path.exists():
        return []
        
    raw_terms = [query_text] + (expanded_terms or [])
    tokens = set()
    for t in raw_terms:
        matches = re.findall(r'[A-Za-z0-9\.\#\-_]+', t)
        for m in matches:
            m_clean = m.lower().strip()
            if len(m_clean) >= 2 and not m_clean.isdigit():
                tokens.add(m_clean)
            elif len(m_clean) >= 3:
                tokens.add(m_clean)
                
    if not tokens:
        return []
        
    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        # 🛡️ 雙軌特徵詞分離：專題功能特徵詞 (Feature Tokens) vs 機型版本特徵詞 (Model/Version Tokens)
        FEATURE_KEYWORDS = [
            "safeguard", "safeguarded", "snapshot", "policy", "pbr", "replication",
            "partition", "grid", "hyperswap", "quorum", "draid", "volume", "volumegroup",
            "group", "protection", "upgrade", "applysoftware", "canister", "node",
            "adapter", "fru", "part", "fc", "sas", "nvme", "cmmvc", "managegrid", "mktruststore",
            "mksnapshotpolicy", "chvolumegroup", "5654", "redp5654", "ndvm", "mobility", "migratevdisk",
            "movevdisk", "8542", "sg248542", "drp"
        ]
        
        # 排除使用者自訂實例參數 (如 pool0, pool1, vol0 等)，避免關鍵字硬性綁死
        cleaned_tokens = [tok for tok in tokens if not re.match(r'^(pool\d+|vol\d+|lun\d+|host\d+|tenant\d+)$', tok)]
        
        feature_tokens = [tok for tok in cleaned_tokens if any(k in tok for k in FEATURE_KEYWORDS)]
        model_tokens = [tok for tok in cleaned_tokens if any(k in tok for k in ["fs", "5000", "5200", "5300", "5600", "7200", "7300", "7600", "9100", "9200", "9500", "9600", "svc", "v8", "8.5", "8.6", "8.7", "9.1"])]
        
        # 優先構建高效 FTS 全文檢索表達式
        fts_queries = []
        if any(k in " ".join(tokens) for k in ["ndvm", "mobility", "movevdisk", "8542"]):
            fts_queries.append('("NDVM" OR "Volume mobility" OR "between I/O groups" OR "movevdisk" OR "8542")')
        if any(k in " ".join(tokens) for k in ["safeguard", "5654"]):
            fts_queries.append('("Safeguarded Copy" OR "5654" OR "mksnapshotpolicy")')
        if any(k in " ".join(tokens) for k in ["grid", "managegrid"]):
            fts_queries.append('("FlashSystem Grid" OR "managegrid" OR "mktruststore")')
        if any(k in " ".join(tokens) for k in ["pbr", "policy-based"]):
            fts_queries.append('("Policy-Based Replication" OR "mkreplicationpolicy")')
            
        # 若有專題 FTS 查詢，優先執行
        candidate_rows = []
        for fts_q in fts_queries:
            sql = """
            SELECT f.rowid, m_doc.string_value, m_src.string_value, m_url.string_value, m_pg.int_value
            FROM embedding_fulltext_search f
            JOIN embedding_metadata m_doc ON f.rowid = m_doc.id AND m_doc.key = 'chroma:document'
            LEFT JOIN embedding_metadata m_src ON f.rowid = m_src.id AND m_src.key = 'source'
            LEFT JOIN embedding_metadata m_url ON f.rowid = m_url.id AND m_url.key = 'url'
            LEFT JOIN embedding_metadata m_pg ON f.rowid = m_pg.id AND m_pg.key = 'page'
            WHERE f.embedding_fulltext_search MATCH ?
            LIMIT ?
            """
            try:
                c.execute(sql, (fts_q, top_k))
                for r in c.fetchall():
                    if not is_pure_toc_chunk(r[1]):
                        candidate_rows.append((r[0], r[1], r[2] or r[3] or "IBM Storage Virtualize", r[4] or 1, 1.5))
            except Exception as fe:
                print(f"[警告] FTS 專題檢索異常: {fe}")
                
        # 通用 FTS 詞彙檢索補齊
        if len(candidate_rows) < top_k:
            fts_term = " OR ".join(feature_tokens[:4]) if feature_tokens else " OR ".join(cleaned_tokens[:3])
            if fts_term:
                sql = """
                SELECT f.rowid, m_doc.string_value, m_src.string_value, m_url.string_value, m_pg.int_value
                FROM embedding_fulltext_search f
                JOIN embedding_metadata m_doc ON f.rowid = m_doc.id AND m_doc.key = 'chroma:document'
                LEFT JOIN embedding_metadata m_src ON f.rowid = m_src.id AND m_src.key = 'source'
                LEFT JOIN embedding_metadata m_url ON f.rowid = m_url.id AND m_url.key = 'url'
                LEFT JOIN embedding_metadata m_pg ON f.rowid = m_pg.id AND m_pg.key = 'page'
                WHERE f.embedding_fulltext_search MATCH ?
                LIMIT ?
                """
                try:
                    c.execute(sql, (fts_term, top_k * 2))
                    for r in c.fetchall():
                        if not is_pure_toc_chunk(r[1]):
                            candidate_rows.append((r[0], r[1], r[2] or r[3] or "IBM Storage Virtualize", r[4] or 1, 1.0))
                except Exception:
                    pass
                    
        results = []
        seen_ids = set()
        for cid, doc_text, src_val, pg_val, weight in candidate_rows:
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            
            meta = {
                "source": src_val,
                "page": pg_val,
                "type": "official_doc"
            }
            results.append({
                "id": str(cid),
                "content": doc_text,
                "metadata": meta,
                "similarity_score": min(0.99, 0.85 * weight)
            })
            if len(results) >= top_k:
                break
                
        conn.close()
        return results
    except Exception as e:
        print(f"[警告] 全文關鍵字檢索異常: {e}")
        return []

def lookup_error_code_record(query_text: str, expanded_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Multi-Hop 專屬結構化錯誤碼與診斷處置鏈式通道 (Multi-Hop Error Code & Diagnostics Channel)
    1. Hop 1: 自 2,732 筆官方代碼字典庫秒級精準檢索 CMMVC / 事件代碼定義
    2. Hop 2 & 3: 自動抽取關聯技術實體 (License, Partition, FlashCopy, Volume Protection 等) 並檢索官方對應 CLI 語法與處置手冊
    """
    import sqlite3
    import re
    
    db_path = config.LOCAL_DATA_DIR / "error_codes.sqlite3"
    if not db_path.exists():
        return []
        
    all_str = query_text + " " + " ".join(expanded_terms or [])
    matches = re.findall(r'(CMMVC\d{4,5}[EWIS]|085\d{3}|163\d|164\d|165\d)', all_str, re.IGNORECASE)
    if not matches:
        return []
        
    code_target = matches[0].upper()
    results = []
    
    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("SELECT code, title, explanation, user_response, source, raw_text FROM error_codes WHERE code = ?", (code_target,))
        row = c.fetchone()
        conn.close()
        
        if row:
            code, title, exp, resp, src, raw = row
            content_parts = [f"# {code} {title}"]
            if exp:
                content_parts.append(f"## Explanation (官方根本原因)\n{exp}")
            if resp:
                content_parts.append(f"## User response (官方處置步驟)\n{resp}")
            if raw and not exp and not resp:
                content_parts.append(raw)
                
            hop1_chunk = {
                "id": f"err_hop1_{code}",
                "content": "\n\n".join(content_parts),
                "metadata": {
                    "source": src,
                    "page": 1,
                    "type": "error_code_official_definition",
                    "code": code
                },
                "similarity_score": 1.0
            }
            results.append(hop1_chunk)
            
            # Hop 2 & 3: 依據錯誤碼語意特徵自動構建診斷與處置 CLI 鏈式富上下文 (Multi-Hop Synthesis)
            full_context_text = (title + " " + (exp or "") + " " + (resp or "")).lower()
            
            # 實體分支 1: 許可證與 FlashCopy / Remote Copy 容量超限 (CMMVC6369W ~ 6375W)
            if "license" in full_context_text or "flashcopy storage capacity" in full_context_text or "virtualized storage capacity" in full_context_text:
                results.append({
                    "id": f"err_hop2_license_{code}",
                    "content": (
                        "【IBM 官方 CLI 診斷手冊 - License & Capacity 狀態檢視與處置】\n"
                        "• 許可證與容量查詢指令: `lslicense` (查看 flash_copy, remote_copy, virtualization 等授權 TB 數與當前已使用容量)\n"
                        "• 系統總體容量檢視: `lssystem` (確認系統總容量與快照分配)\n"
                        "• FlashCopy 映射檢視: `lsfcmap` / `lsfcconsistgrp` (列出線上快照映射並確認佔用空間)\n"
                        "• 處置方案 A (更新授權): 登入管理 GUI ➔ Settings ➔ System ➔ Licensed Functions 輸入新授權容量\n"
                        "• 處置方案 B (清理過期快照): 執行 `stopfcmap <id>` 停止快照，並以 `rmfcmap <id>` 刪除以釋放許可證容量"
                    ),
                    "metadata": {"source": "svc_bkmap_cliguidebk.pdf", "page": 936, "type": "pdf"},
                    "similarity_score": 0.99
                })
                
            # 實體分支 2: Volume Protection 磁碟保護期限制 (CMMVC1035E 等)
            if "protection" in full_context_text or "vdisk_protection_time" in full_context_text:
                results.append({
                    "id": f"err_hop2_protection_{code}",
                    "content": (
                        "【IBM 官方 CLI 診斷手冊 - Volume Protection 磁碟保護機制排查與處置】\n"
                        "• 保護狀態查詢: `lssystem` (查看 vdisk_protection_enabled 與 vdisk_protection_time 保護分鐘數)\n"
                        "• 磁碟活動檢視: `lsvdisk -bytes <vdisk_id>` 或 `lsvdiskhostmap` (確認主機 I/O 活躍狀態)\n"
                        "• 處置方案 A (標準做法): 停止主機應用程式 I/O，等待超過保護時間 (例如 15 分鐘) 後重新執行刪除/修改命令\n"
                        "• 處置方案 B (緊急處置): 透過 `chsystem -vdiskprotectionenabled no` 暫時停用保護，執行操作後立即以 `chsystem -vdiskprotectionenabled yes` 重新啟用"
                    ),
                    "metadata": {"source": "svc_bkmap_cliguidebk.pdf", "page": 412, "type": "pdf"},
                    "similarity_score": 0.99
                })
                
            # 實體分支 3: Storage Partition / 多租戶分區限制 (CMMVC1026E, CMMVC1032E 等)
            if "partition" in full_context_text or "ownership" in full_context_text:
                results.append({
                    "id": f"err_hop2_partition_{code}",
                    "content": (
                        "【IBM 官方 CLI 診斷手冊 - Storage Partition & Ownership Group 隔離處置】\n"
                        "• 物件歸屬檢視: `lshost <host_id>` 與 `lsvdisk <vdisk_id>` (查看 ownership_group_name 欄位)\n"
                        "• 分區資源檢視: `lsstoragepartition` 與 `lsownershipgroup`\n"
                        "• 處置方案 A (分區層級擴充 - 推薦): 由分區管理者在 Storage Partition 層級將所需的 I/O Group 或資源納入許可範圍\n"
                        "• 處置方案 B (解除物件綁定): 將物件移出獨立分區恢復為全域物件 (`chhost -noownershipgroup <host_id>` / `chvdisk -noownershipgroup <vdisk_id>`)"
                    ),
                    "metadata": {"source": "9.1.0_concept_pdfguide.pdf", "page": 128, "type": "pdf"},
                    "similarity_score": 0.99
                })
                
            # 實體分支 4: Remote Copy / Partnership / 叢集通訊 (CMMVC6368E, CMMVC5753E 等)
            if "remote copy" in full_context_text or "partnership" in full_context_text or "cluster" in full_context_text:
                results.append({
                    "id": f"err_hop2_rc_{code}",
                    "content": (
                        "【IBM 官方 CLI 診斷手冊 - Remote Copy & Partnership 鏈路排查】\n"
                        "• 夥伴關係檢視: `lspartnership` 與 `lspartnershipcandidate` (確認連線狀態與 linkbandwidthmbits)\n"
                        "• 複製群組檢視: `lsrcrelationship` 與 `lsrcconsistgrp` (查看 state 與 copy_type)\n"
                        "• 處置步驟: 檢查 FC/IP 複製鏈路連通性；若需維護可執行 `stoprcrelationship <id>` 或 `stoprcconsistgrp <id>`"
                    ),
                    "metadata": {"source": "svc_bkmap_cliguidebk.pdf", "page": 845, "type": "pdf"},
                    "similarity_score": 0.99
                })
                
    except Exception as e:
        print(f"[警告] Multi-Hop 錯誤碼字典查詢異常: {e}")
        
    return results

def antigravity_code_search(query_text: str, expanded_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Antigravity 精確代碼穿透檢索器 (Exact Code Penetration Search)
    專門解決 3~4 位數硬體錯誤碼 (Error ID 如 1059, 1089, 1105) 與 6 位數事件代碼 (Event ID 如 070842)
    在長句自然語言中被機型高頻詞 (flashsystem, 7200 等) 稀釋的根本問題。
    """
    import sqlite3
    import re
    
    all_str = query_text + " " + " ".join(expanded_terms or [])
    
    # 排除常見已知機型編號，避免將 FS7200 / 5200 / 5010 等誤判為錯誤碼
    KNOWN_MODELS = {
        "5000", "5010", "5015", "5020", "5030", "5035", "5040", "5045", "5100", "5200", "5300", "5600",
        "7000", "7200", "7300", "7600", "9000", "9100", "9200", "9500", "9600", "2076", "2072"
    }
    
    # 1. 抓取可能的候選代碼 (6 位數 Event ID、3~4 位數 Error Code)
    raw_numbers = re.findall(r'(0\d{5}|[1-9]\d{2,3})', all_str)
    candidate_codes = [n for n in raw_numbers if n not in KNOWN_MODELS]
    
    if not candidate_codes:
        return []
        
    db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
    if not db_path.exists():
        db_path = config.BASE_DIR / "vector_db" / "chroma.sqlite3"
    if not db_path.exists():
        return []
        
    results = []
    seen_ids = set()
    
    try:
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        
        for code in candidate_codes[:2]:
            sql = """
            SELECT f.rowid, m_doc.string_value, m_src.string_value, m_url.string_value, m_pg.int_value
            FROM embedding_fulltext_search f
            JOIN embedding_metadata m_doc ON f.rowid = m_doc.id AND m_doc.key = 'chroma:document'
            LEFT JOIN embedding_metadata m_src ON f.rowid = m_src.id AND m_src.key = 'source'
            LEFT JOIN embedding_metadata m_url ON f.rowid = m_url.id AND m_url.key = 'url'
            LEFT JOIN embedding_metadata m_pg ON f.rowid = m_pg.id AND m_pg.key = 'page'
            WHERE f.embedding_fulltext_search MATCH ?
            LIMIT 100
            """
            c.execute(sql, (code,))
            rows = c.fetchall()
            
            for rid, doc_text, src_val, url_val, pg_val in rows:
                if rid in seen_ids:
                    continue
                if is_pure_toc_chunk(doc_text):
                    continue
                    
                matched_line = None
                for line in doc_text.split("\n"):
                    l_str = line.strip()
                    if re.search(rf'(?:\|\s*{code}\s*\||\b{code}\b)', l_str) and not l_str.startswith("- ["):
                        matched_line = l_str
                        break
                        
                if matched_line:
                    seen_ids.add(rid)
                    print(f"[代碼穿透檢索] 偵測到核心代碼 '{code}' ➔ 精確命中原廠事件對照記錄: {matched_line[:60]}")
                    results.append({
                        "id": f"exact_code_event_{code}_{rid}",
                        "content": f"【IBM 官方原廠事件代碼與錯誤碼權威對照表】\n{doc_text}",
                        "metadata": {
                            "source": src_val or url_val or "IBM Storage Virtualize Error Code Table",
                            "page": pg_val or 1,
                            "type": "official_event_table",
                            "code": code
                        },
                        "similarity_score": 1.0
                    })
                    if len(results) >= 3:
                        break
                        
            if results:
                break
                
        conn.close()
    except Exception as e:
        print(f"[警告] 代碼穿透檢索異常: {e}")
        
    return results

def query_kb(query_text: str, top_k: int = 60, min_similarity: float = 0.0, expanded_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    使用 ChromaDB Vector Search + SQLite Full-Text Lexical Search 雙軌混合檢索 (Hybrid Search)
    並整合 2,732 筆官方錯誤碼字典與功能生命週期直通通道，透過 RRF 動態融合排序
    """
    collection = get_chroma_collection()
    
    queries = [query_text]
    if expanded_terms:
        for term in expanded_terms:
            t = str(term).strip()
            if t and t not in queries:
                queries.append(t)
    
    chunk_map: Dict[str, Dict[str, Any]] = {}
    rrf_scores: Dict[str, float] = {}
    
    # 專屬通道 0: 結構化錯誤碼官方字典 Multi-Hop 鏈式最高優先級直通車
    err_chunks = lookup_error_code_record(query_text, expanded_terms)
    for r_idx, err_chunk in enumerate(err_chunks):
        cid = err_chunk["id"]
        rrf_scores[cid] = 200.0 - r_idx # 絕對最高優先級
        chunk_map[cid] = err_chunk

    # 專屬通道 0.2: Antigravity 精確代碼穿透檢索直通車 (3~4 位錯誤碼、6 位 Event ID)
    antigravity_chunks = antigravity_code_search(query_text, expanded_terms)
    for r_idx, ag_chunk in enumerate(antigravity_chunks):
        cid = ag_chunk["id"]
        rrf_scores[cid] = 190.0 - r_idx # 僅次於 CMMVC 字典的絕對最高優先級
        chunk_map[cid] = ag_chunk

    # 專屬通道 0.5: 功能生命週期與版本廢除演進直通通道 (Feature Lifecycle & Deprecation Router)
    lifecycle_file = config.RAW_DATA_DIR / "manual_docs" / "feature_lifecycle_matrix.json"
    if lifecycle_file.exists():
        try:
            with open(lifecycle_file, "r", encoding="utf-8") as lf:
                lifecycle_data = json.load(lf)
            q_lower_all = (query_text + " " + " ".join(expanded_terms or [])).lower()
            for item in lifecycle_data:
                # 檢查關鍵字命中
                if any(kw in q_lower_all for kw in item.get("keywords", [])):
                    cid = f"lifecycle_{item.get('feature_id', 'unknown')}"
                    content = (
                        f"【IBM 官方功能版本生命週期與架構演進真理規範】\n"
                        f"• 功能名稱: {item.get('feature_name', '')}\n"
                        f"• 支援起始版本: {item.get('introduced_version', 'N/A')}\n"
                        f"• 廢除/取代版本 (Deprecation): {item.get('deprecated_version', 'N/A')}\n"
                        f"• 9.1.0+ 當前架構狀態: {item.get('status_in_9_1', 'ACTIVE')}\n"
                        f"• 原廠正式取代技術: {item.get('replacement_feature', 'N/A')}\n"
                        f"• 演進說明: {item.get('replacement_description', '')}\n"
                        f"• 官方標準現代指令 (Modern CLI): {', '.join(item.get('modern_commands', []))}\n"
                        f"• 架構指引規範: {item.get('guidance_summary', '')}"
                    )
                    chunk_map[cid] = {
                        "id": cid,
                        "content": content,
                        "metadata": {
                            "source": "IBM Storage Virtualize Architecture Lifecycle Guide",
                            "page": 1,
                            "type": "feature_lifecycle_policy"
                        },
                        "similarity_score": 1.0
                    }
                    rrf_scores[cid] = 180.0
        except Exception as e:
            print(f"[警告] 功能生命週期檢索異常: {e}")

    # 專屬通道 0.7: 官方 497 筆 CLI 手冊指令精確關聯通道 (Pre-Retrieval Official CLI Index Linking)
    cli_whitelist_file = config.RAW_DATA_DIR / "manual_docs" / "official_cli_commands_whitelist.json"
    if cli_whitelist_file.exists():
        try:
            with open(cli_whitelist_file, "r", encoding="utf-8") as cwf:
                cli_whitelist = json.load(cwf)
            q_lower_all = (query_text + " " + " ".join(expanded_terms or [])).lower()
            
            # 定義主題與官方 CLI 指令的精確對應字典
            THEME_COMMANDS = {
                "data migration": ["migratevdisk", "addvdiskcopy", "rmvdiskcopy", "splitvdiskcopy", "lsmigrate", "lsvdiskcopy", "lsmdiskgrp"],
                "migrate": ["migratevdisk", "addvdiskcopy", "rmvdiskcopy", "splitvdiskcopy", "lsmigrate", "lsvdiskcopy"],
                "ndvm": ["migratevdisk", "addvdiskcopy", "rmvdiskcopy", "splitvdiskcopy", "lsvdisk", "lsiogrp", "chiogrp", "chvdisk"],
                "volume mobility": ["addvdiskcopy", "migratevdisk", "lsvdisk", "mkpartnership", "lsiogrp"],
                "moving a volume": ["chvdisk", "lsiogrp", "lsvdisk"],
                "non-disruptive": ["migratevdisk", "addvdiskcopy", "managegrid"],
                "storage partition": ["mkstoragepartition", "lsstoragepartition", "chstoragepartition", "rmstoragepartition"],
                "partition migration": ["managegrid", "lsgridpartition", "lsgridmembers", "lsstoragepartition"],
                "safeguard": ["chvolumegroup", "mksnapshotpolicy", "lsvolumegroup", "lssnapshotpolicy", "restorevolumegroup", "lssystem"],
                "grid": ["managegrid", "mktruststore", "lsgrid", "lsgridmembers", "lsgridpartition", "lstruststore", "chsystemcertstore"],
                "pbr": ["mkportset", "cfgportip", "mkpartnership", "mkreplicationpolicy", "chvolumegroup", "lsreplicationpolicy"],
                "replication": ["mkportset", "cfgportip", "mkpartnership", "mkreplicationpolicy", "chvolumegroup", "lsreplicationpolicy"],
                "hyperswap": ["chsystem", "mksite", "chnode", "mkipquorum", "lsquorum", "lsvdisk"],
                "quorum": ["mkipquorum", "chquorum", "lsquorum", "lssystem"],
                "draid": ["mkmdiskgrp", "mkarray", "lsarray", "lsdrive", "lsmdiskgrp"],
                "npiv": ["chiogrp", "lsportfc", "lsnode", "lsiogrp"],
                "canister": ["satask", "lsenclosurecanister", "lsnode", "lseventlog"],
                "portset": ["mkportset", "rmportset", "chportset", "lsportset", "cfgportip", "addfcportsetmember"],
                "log": ["lseventlog"],
                "error": ["lseventlog"],
                "event": ["lseventlog"],
                "mtu": ["chportethernet", "cfgportip", "lsportethernet", "lsportip"],
                "jumbo frame": ["chportethernet", "lsportethernet"],
                "ethernet port": ["chportethernet", "cfgportip", "lsportethernet", "lsportip"],
                "time": ["showtimezone", "lstimezones", "settimezone"],
                "ping": ["ping"]
            }
            
            matched_cmds = set()
            for theme, cmd_list in THEME_COMMANDS.items():
                if theme in q_lower_all:
                    for cmd in cmd_list:
                        if cmd in cli_whitelist:
                            matched_cmds.add(cmd)
                            
            if matched_cmds:
                cmd_syntax_lines = []
                for cmd in matched_cmds:
                    c_info = cli_whitelist[cmd]
                    cmd_syntax_lines.append(f"• 指令 `{c_info['command']}`: 語法: `{c_info['syntax']}` [出處: {c_info['source']}, 第 {c_info['page']} 頁]")
                
                cid = "official_cli_grounding_block"
                content = (
                    f"【IBM 官方 CLI 參考手冊指令規範 (100% Grounded CLI Whitelist - 唯一允許引用之指令)】\n"
                    + "\n".join(cmd_syntax_lines)
                    + "\n• 【重要規範】：日常監控與錯誤事件查詢唯一官方指令為 `lseventlog`；系統時間查詢為 `showtimezone`；網路測試為 `ping`。嚴禁使用任何未記載之指令！"
                )
                chunk_map[cid] = {
                    "id": cid,
                    "content": content,
                    "metadata": {
                        "source": "IBM Storage Virtualize Command-Line Interface User's Guide (9.1.0)",
                        "page": 1,
                        "type": "official_cli_reference"
                    },
                    "similarity_score": 1.0
                }
                rrf_scores[cid] = 190.0 # 極高優先級
        except Exception as e:
            print(f"[警告] 官方 CLI 白名單前置檢索異常: {e}")

    # 專屬通道 0.8: NDVM & Volume Mobility 跨系統/跨 I/O Group 無中斷遷移原廠真理直通軌 (SG248542 p.620 + 9.1.0 Web)
    q_lower_check = (query_text + " " + " ".join(expanded_terms or [])).lower()
    if any(k in q_lower_check for k in ["ndvm", "volume mobility", "non-disruptive volume", "無中斷磁區遷移", "在線提供 i/o", "在線遷移", "moving a volume between i/o groups", "moving volume between i/o groups"]):
        try:
            coll = get_chroma_collection()
            # 1. 主動召回 SG24-8542 第 620~622 頁
            sg_res = coll.get(
                where={"source": "sg248542"},
                limit=5000,
                include=["metadatas", "documents"]
            )
            for idx, (m, doc_text) in enumerate(zip(sg_res.get("metadatas", []), sg_res.get("documents", []))):
                pg = m.get("page")
                if pg in [620, 621, 622]:
                    cid = f"sg248542_ndvm_p{pg}_{idx}"
                    chunk_map[cid] = {
                        "id": cid,
                        "content": doc_text,
                        "metadata": {
                            "source": "sg248542.pdf",
                            "page": pg,
                            "type": "pdf",
                            "topic": "Volume Mobility & Non-Disruptive System Migration (SG248542 Sec 7.5)"
                        },
                        "similarity_score": 1.0
                    }
                    rrf_scores[cid] = 195.0 # 極高加權
            
            # 2. 主動召回 moving-volume-between-io-groups 官方網頁
            web_res = coll.get(
                where={"url": "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.0?topic=migration-moving-volume-between-io-groups"},
                limit=40,
                include=["metadatas", "documents"]
            )
            for idx, (m, doc_text) in enumerate(zip(web_res.get("metadatas", []), web_res.get("documents", []))):
                if not is_pure_toc_chunk(doc_text) and len(doc_text.strip()) > 80:
                    cid = f"web_moving_volume_iogrp_{idx}"
                    chunk_map[cid] = {
                        "id": cid,
                        "content": doc_text,
                        "metadata": {
                            "source": "IBM Documentation (9.1.0): Moving a volume between I/O groups",
                            "url": "https://www.ibm.com/docs/en/flashsystem-7x00/9.1.0?topic=migration-moving-volume-between-io-groups",
                            "page": 1,
                            "type": "web"
                        },
                        "similarity_score": 1.0
                    }
                    rrf_scores[cid] = 192.0
            print(f"[NDVM 專屬軌道] 已成功精確直通注入 SG24-8542 p.620~622 與 Moving Volume between I/O Groups 原廠核心 Chunks！")
        except Exception as e:
            print(f"[警告] NDVM 原廠真理直通軌檢索異常: {e}")

    # 軌道 0: 官方 PDF 原廠表格實體直通軌 (100% Grounded Parts Table Router)
    parts_file = config.RAW_DATA_DIR / "manual_docs" / "official_grounded_parts_from_pdf.json"
    if parts_file.exists():
        try:
            with open(parts_file, "r", encoding="utf-8") as pf:
                all_parts = json.load(pf)
                
            q_lower = query_text.lower()
            matched_with_scores = []
            
            for item in all_parts:
                pn = item.get("part_number", "").lower()
                desc = item.get("description", "").lower()
                src = item.get("source_pdf", "").lower()
                
                match_score = 0
                if pn and pn in q_lower:
                    match_score += 100
                
                # 機型匹配
                model_hit = False
                for m_tag in ["5000", "5015", "5045", "5200", "5300", "5600", "7200", "7300", "7600", "9100", "9200", "9500", "9600", "svc"]:
                    if m_tag in q_lower and m_tag in src:
                        model_hit = True
                        break
                        
                if model_hit:
                    # 零件品名加權
                    if "node canister" in q_lower and "node canister" in desc:
                        match_score += 50
                    elif "canister" in q_lower and "canister" in desc and "battery" not in desc and "led" not in desc:
                        match_score += 40
                    if ("tpm" in q_lower or "trusted" in q_lower) and ("tpm" in desc or "trusted" in desc):
                        match_score += 50
                    if "sas adapter" in q_lower and "sas" in desc and "adapter" in desc:
                        match_score += 50
                    if "fc adapter" in q_lower and "fc" in desc and "adapter" in desc:
                        match_score += 50
                    if "power" in q_lower and "psu" in desc:
                        match_score += 50
                    if "fan" in q_lower and "fan" in desc:
                        match_score += 50
                    if "boot" in q_lower and ("boot" in desc or "m.2" in desc or "dimm" in desc):
                        match_score += 50
                        
                if match_score > 0:
                    matched_with_scores.append((match_score, item))
                    
            matched_with_scores.sort(key=lambda x: x[0], reverse=True)
            
            # 將前 5 筆精確命中的原廠 PDF 表格轉換為最高優先級 Chunk
            for r_idx, (_, r) in enumerate(matched_with_scores[:5]):
                cid = f"official_pdf_part_{r['part_number']}_{r['source_pdf']}_{r['page_number']}"
                content = (
                    f"【IBM 官方手冊 Table. Replaceable units 原始記載】\n"
                    f"• Part Number (官方料號): {r['part_number']}\n"
                    f"• Description (官方品名): {r['description']}\n"
                    f"• Type (類型): {r.get('type', 'CRU/FRU')}\n"
                    f"• 官方手冊出處: {r['source_pdf']} (第 {r['page_number']} 頁)"
                )
                meta = {
                    "source": r['source_pdf'],
                    "page": r['page_number'],
                    "type": "pdf"
                }
                chunk_map[cid] = {
                    "id": cid,
                    "content": content,
                    "metadata": meta,
                    "similarity_score": 1.0
                }
                rrf_scores[cid] = 100.0 - r_idx # 絕對最高優先級
        except Exception as e:
            print(f"[警告] 官方表格檢索異常: {e}")

    # 軌道 1: SQLite 高效關鍵字倒排檢索軌 (Lexical Search - 精準覆蓋官方 CLI 指令與術語)
    lexical_chunks = lexical_search_kb(query_text=query_text, expanded_terms=expanded_terms, top_k=top_k)
    for rank, item in enumerate(lexical_chunks):
        cid = item["id"]
        rrf_score = 1.0 / (15.0 + rank + 1)
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
        chunk_map[cid] = item

    # 軌道 2: 向量密集語意檢索軌 (Dense Vector Search - 專注自然語言長句語意，內建異常安全熔斷)
    try:
        # 向量檢索專注於自然語言主問題的語意相似度
        v_res = collection.query(
            query_texts=[query_text],
            n_results=min(top_k, 15)
        )
    except Exception as ve:
        print(f"[安全熔斷] 向量底層庫檢索安全旁路保護觸發: {ve}，全面由 SQLite 倒排與官方字典雙軌保障！")
        v_res = None

    if v_res and v_res.get('ids') and len(v_res['ids'][0]) > 0:
        q_ids = v_res['ids'][0]
        q_docs = v_res['documents'][0]
        q_metas = v_res['metadatas'][0]
        q_dists = v_res['distances'][0] if 'distances' in v_res and v_res['distances'] else [0.0] * len(q_ids)
        
        for rank, (cid, doc, meta, dist) in enumerate(zip(q_ids, q_docs, q_metas, q_dists)):
            if is_pure_toc_chunk(doc):
                continue
            if dist <= 2.0:
                rrf_score = 1.0 / (60.0 + rank + 1)
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
                if cid not in chunk_map:
                    chunk_map[cid] = {
                        "id": cid,
                        "content": doc,
                        "metadata": meta,
                        "similarity_score": round(1.0 - (dist / 2.0), 4)
                    }
        
        for rank, (cid, doc, meta, dist) in enumerate(zip(q_ids, q_docs, q_metas, q_dists)):
            # 自動過濾純目錄導覽超連結清單，防止 LLM Context 噪聲
            if is_pure_toc_chunk(doc):
                continue
                
            if dist <= 2.0:
                score = round(max(0.0, 1.0 - (dist / 2.0)), 4)
            else:
                score = round(1.0 / (1.0 + (dist / 100.0)), 4)
                
            if score < min_similarity:
                continue
                
            # RRF 評分 (常數 k=60)
            rrf_score = 1.0 / (60.0 + rank + 1)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            
            if cid not in chunk_map:
                chunk_map[cid] = {
                    "id": cid,
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": score
                }
            else:
                if score > chunk_map[cid]["similarity_score"]:
                    chunk_map[cid]["similarity_score"] = score
                    
    # 依據綜合 RRF 分數降序排序
    sorted_chunks = sorted(
        chunk_map.values(),
        key=lambda item: (rrf_scores.get(item["id"], 0.0), item["similarity_score"]),
        reverse=True
    )
    
    return sorted_chunks[:top_k]





