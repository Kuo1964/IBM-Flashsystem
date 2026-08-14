"""
IBM FlashSystem 專家系統 - 向量資料庫與 Embedding 管理器
使用 ChromaDB 持久化儲存區與 Ollama Embedding (nomic-embed-text)
"""

import time
from typing import List, Dict, Any
import chromadb
import httpx
import config

class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    """自訂 ChromaDB 使用的 Ollama Embedding 介面"""
    def __init__(self, model_name: str = config.EMBEDDING_MODEL, host: str = config.OLLAMA_HOST):
        self.model_name = model_name
        self.host = host

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                response = httpx.post(
                    f"{self.host}/api/embeddings",
                    json={"model": self.model_name, "prompt": text},
                    timeout=30.0
                )
                if response.status_code == 200:
                    embeddings.append(response.json()["embedding"])
                else:
                    embeddings.append([0.0] * 768)
            except Exception as e:
                err_str = str(e)
                if "Operation not permitted" in err_str or "[Errno 1]" in err_str:
                    print(f"[警告] 沙箱限制阻止了存取本地 Ollama 服務 ({self.host})。請確保在 BypassSandbox 模式或真實終端機中執行。")
                elif "Connection refused" in err_str or "ConnectError" in err_str:
                    print(f"[警告] 無法連線至 Ollama 服務 ({self.host})，請確認 Ollama 服務是否已啟動 (ollama serve)。")
                else:
                    print(f"[錯誤] 生成 Embedding 失敗: {e}")
                embeddings.append([0.0] * 768)
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
    """將文字 Chunk 與圖表摘要片段批量寫入向量庫 (支援重試機制與小批次)"""
    if not chunks:
        return

    collection = get_chroma_collection()
    
    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    # 使用較小的批次 (50 筆) 並加入重試機制，防止密集寫入觸發 HNSW compaction 錯誤
    batch_size = 50
    total = len(ids)

    for i in range(0, total, batch_size):
        sub_ids = ids[i:i+batch_size]
        sub_docs = documents[i:i+batch_size]
        sub_metas = metadatas[i:i+batch_size]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                collection.upsert(
                    ids=sub_ids,
                    documents=sub_docs,
                    metadatas=sub_metas
                )
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  [警告] 向量寫入暫時失敗，進行第 {attempt + 1} 次重試: {e}")
                    time.sleep(1.0)
                else:
                    print(f"  [錯誤] 向量寫入失敗 ({len(sub_ids)} 筆): {e}")

    print(f"  [成功] 已寫入/更新 {total} 筆記錄至向量資料庫。")

def delete_source_from_db(source_name: str):
    """刪除指定來源資料（用於文件重新寫入時的舊記錄清除）"""
    collection = get_chroma_collection()
    try:
        collection.delete(where={"source": source_name})
        print(f"  [資訊] 已清除來源 '{source_name}' 之舊向量記錄。")
    except Exception as e:
        print(f"  [提示] 清除舊資料時無符合記錄 ({source_name}): {e}")

def query_kb(query_text: str, top_k: int = 8, min_similarity: float = 0.75) -> List[Dict[str, Any]]:
    """查詢 FlashSystem 專家知識庫 (包含相似度門檻過濾與確定性二次排序)"""
    collection = get_chroma_collection()
    # 擴大內部檢索量，利於門檻過濾
    fetch_k = max(top_k * 2, 10)
    results = collection.query(
        query_texts=[query_text],
        n_results=fetch_k
    )

    formatted_results = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        ids = results["ids"][0] if "ids" in results else [f"id_{i}" for i in range(len(docs))]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
        
        for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
            score = round(1.0 - dist, 4) if dist <= 1.0 else 0.0
            # 相似度門檻過濾 (剔除低於 75% 的不相干噪訊)
            if score >= min_similarity:
                formatted_results.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "similarity_score": score
                })

    # 確定性二次排序：優先按分數降序，分數相同按 chunk_id 字典序排序，消除 HNSW 隨機性
    formatted_results.sort(
        key=lambda x: (x["similarity_score"], x["metadata"].get("source", ""), x["id"]),
        reverse=True
    )

    # 截取要求的 top_k 筆數
    return formatted_results[:top_k]

