import chromadb
import config
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

def get_chroma_collection():
    """取得或建立 ChromaDB 集合"""
    client = chromadb.PersistentClient(path=str(config.VECTOR_DB_DIR))
    embedding_fn = OllamaEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="ibm_flashsystem_kb",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection

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
    """
    判斷 chunk 是否為純目錄/導覽列超連結清單 (TOC Link Dump)
    避免大量無技術內容的目錄清單污染 LLM Context 與引發幻覺
    """
    if not text:
        return False
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 3:
        return False
    link_lines = [l for l in lines if l.startswith('- [') or l.startswith('* [') or ('](/docs/' in l and len(l) < 120)]
    return (len(link_lines) / len(lines)) >= 0.5

def lexical_search_kb(query_text: str, expanded_terms: List[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    透過 SQLite 全文關鍵字精準匹配 (Exact Lexical & Token Search)
    專門解決數字、料號 (Part Numbers / FRU)、Feature Codes、硬體零件代碼在密集向量中語意稀釋的問題
    """
    import sqlite3
    import re
    
    db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
    if not db_path.exists():
        return []
        
    raw_terms = [query_text] + (expanded_terms or [])
    tokens = set()
    for t in raw_terms:
        matches = re.findall(r'[A-Za-z0-9\.\#\-]+', t)
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
        
        important_tokens = [tok for tok in tokens if any(k in tok for k in ["7.68", "240", "nvme", "m.2", "fru", "part", "adapter", "fc", "32", "64", "sas", "drive", "ssd", "canister", "dimm", "03", "ag0", "cmmvc"])]
        if not important_tokens:
            important_tokens = list(tokens)[:4]
            
        candidate_rows = []
        for i in range(len(important_tokens), 0, -1):
            subset = important_tokens[:i]
            where_conditions = ["string_value LIKE ?" for _ in subset]
            where_clause = " AND ".join(where_conditions)
            params = [f"%{tok}%" for tok in subset]
            
            sql = f"""
            SELECT id, string_value 
            FROM embedding_metadata 
            WHERE key = 'chroma:document' AND {where_clause}
            LIMIT {top_k * 3};
            """
            c.execute(sql, params)
            rows = c.fetchall()
            if rows:
                for r in rows:
                    # 自動過濾純目錄導覽連結 Chunk，保留真正含有技術正文的段落
                    if not is_pure_toc_chunk(r[1]):
                        candidate_rows.append(r)
                if len(candidate_rows) >= top_k:
                    break
                    
        results = []
        seen_ids = set()
        for cid, doc_text in candidate_rows:
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            
            c.execute("SELECT key, string_value, int_value FROM embedding_metadata WHERE id = ?", (cid,))
            meta_rows = c.fetchall()
            meta = {}
            for k, s_val, i_val in meta_rows:
                if k == 'chroma:document': continue
                meta[k] = s_val if s_val is not None else i_val
                
            results.append({
                "id": str(cid),
                "content": doc_text,
                "metadata": meta,
                "similarity_score": 0.95
            })
            
        conn.close()
        return results[:top_k]
    except Exception as e:
        print(f"[警告] 全文關鍵字檢索異常: {e}")
        return []

def lookup_error_code_record(query_text: str, expanded_terms: List[str] = None) -> Optional[Dict[str, Any]]:
    """
    專屬結構化錯誤碼通道 (Structured Error Code Channel)
    直接自 2,732 筆官方代碼字典庫秒級精準檢索 CMMVC / 事件代碼
    """
    import sqlite3
    import re
    
    db_path = config.LOCAL_DATA_DIR / "error_codes.sqlite3"
    if not db_path.exists():
        return None
        
    all_str = query_text + " " + " ".join(expanded_terms or [])
    matches = re.findall(r'(CMMVC\d{4,5}[EWIS])', all_str, re.IGNORECASE)
    if not matches:
        return None
        
    code_target = matches[0].upper()
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
                content_parts.append(f"## Explanation\n{exp}")
            if resp:
                content_parts.append(f"## User response\n{resp}")
            if raw and not exp and not resp:
                content_parts.append(raw)
                
            return {
                "id": f"err_{code}",
                "content": "\n\n".join(content_parts),
                "metadata": {
                    "source": src,
                    "page": 1,
                    "type": "error_code_official_definition",
                    "code": code
                },
                "similarity_score": 1.0
            }
    except Exception as e:
        print(f"[警告] 錯誤碼字典查詢異常: {e}")
    return None

def query_kb(query_text: str, top_k: int = 25, min_similarity: float = 0.0, expanded_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    使用 ChromaDB Vector Search + SQLite Full-Text Lexical Search 雙軌混合檢索 (Hybrid Search)
    並整合 2,732 筆官方錯誤碼字典資源組通道，透過 RRF 動態融合排序
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
    
    # 專屬通道 0: 結構化錯誤碼官方字典最高優先級直通車
    err_chunk = lookup_error_code_record(query_text, expanded_terms)
    if err_chunk:
        cid = err_chunk["id"]
        rrf_scores[cid] = 10.0
        chunk_map[cid] = err_chunk

    # 軌道 1: 全文關鍵字精準檢索軌 (Lexical Search - 專治數字與料號表格)
    lexical_hits = lexical_search_kb(query_text, expanded_terms, top_k=15)
    for rank, item in enumerate(lexical_hits):
        cid = item["id"]
        # 精準關鍵字命中給予極高 RRF 加權 (k=15)
        rrf_score = 1.0 / (15.0 + rank + 1)
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
        chunk_map[cid] = item

    # 軌道 2: 向量密集語意檢索軌 (Dense Vector Search)
    for q_idx, q in enumerate(queries):
        res = None
        for n_res in [top_k, 15, 8, 5]:
            try:
                res = collection.query(
                    query_texts=[q],
                    n_results=n_res
                )
                if res and res.get('ids') and len(res['ids'][0]) > 0:
                    break
            except Exception as e:
                continue
                
        if not res or not res.get('ids') or len(res['ids'][0]) == 0:
            continue
            
        q_ids = res['ids'][0]
        q_docs = res['documents'][0]
        q_metas = res['metadatas'][0]
        q_dists = res['distances'][0] if 'distances' in res and res['distances'] else [0.0] * len(q_ids)
        
        for rank, (cid, doc, meta, dist) in enumerate(zip(q_ids, q_docs, q_metas, q_dists)):
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





