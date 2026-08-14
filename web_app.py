"""
IBM FlashSystem 專家系統 - 雲端問答入口 (Web Cloud Portal) REST API 伺服器
提供安全的 RAG 問答、語意快取、速率防護、併發排隊佇列與靜態圖片預覽服務
"""

import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

import config
import vector_store
import ingest

app = FastAPI(
    title="IBM FlashSystem 專家系統 - 雲端問答入口 API",
    description="提供全團隊同仁使用的本地/雲端 RAG 問答檢索服務",
    version="2.0.0"
)

# 跨網域 CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 併發排隊佇列與安全控制 (最多同時 3 筆 LLM 推理，防止本機顯示卡/CPU 爆掉)
query_semaphore = asyncio.Semaphore(3)

# 語意快取字典: {query_text: {"response": dict, "timestamp": float}}
QUERY_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 快取有效時間 (秒)

# 同事發問速率限制 (Rate Limiter): {ip: [timestamp, ...]}
USER_RATE_LIMITS: Dict[str, List[float]] = {}
MAX_REQUESTS_PER_MINUTE = 10  # 單一 IP 每分鐘上限

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

def check_rate_limit(client_ip: str):
    """檢查請求速率防護 (Rate Limiting)"""
    now = time.time()
    timestamps = USER_RATE_LIMITS.get(client_ip, [])
    # 移除 1 分鐘以前的舊記錄
    timestamps = [ts for ts in timestamps if now - ts < 60]
    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"提問頻率過高！每位同仁每分鐘上限為 {MAX_REQUESTS_PER_MINUTE} 次，請稍候再試。"
        )
    timestamps.append(now)
    USER_RATE_LIMITS[client_ip] = timestamps

@app.get("/", response_class=HTMLResponse)
async def serve_portal_ui():
    """提供 Web Portal 前端介面主頁"""
    static_file = config.BASE_DIR / "static" / "index.html"
    if static_file.exists():
        with open(static_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>IBM FlashSystem 專家系統 Web Portal 服務已啟動</h1>"

@app.get("/api/stats")
async def get_kb_statistics():
    """取得知識庫統計資訊"""
    manifest = ingest.load_manifest()
    pdf_count = sum(1 for v in manifest.values() if v.get("type") == "pdf")
    url_count = sum(1 for v in manifest.values() if v.get("type") == "url")
    total_chunks = sum(v.get("chunks_count", 0) for v in manifest.values())

    return {
        "status": "online",
        "pdf_count": pdf_count,
        "url_count": url_count,
        "manifest_entries": len(manifest),
        "total_chunks_estimate": total_chunks,
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_model": config.LLM_MODEL,
        "vision_model": config.VISION_MODEL
    }

@app.post("/api/query")
async def query_knowledge_base(req: QueryRequest, request: Request):
    """
    RAG 問答檢索端點 (含語意快取、速率限制與安全排隊佇列)
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    query_text = req.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="提問內容不能為空")

    if len(query_text) > 500:
        raise HTTPException(status_code=400, detail="提問內容過長，請限制在 500 字以內")

    # 1. 檢查語意快取 (Cache) - 命中直接回傳，零 Token 消耗
    now = time.time()
    cache_key = f"{query_text}_{req.top_k}"
    if cache_key in QUERY_CACHE:
        cached_item = QUERY_CACHE[cache_key]
        if now - cached_item["timestamp"] < CACHE_TTL:
            res_data = dict(cached_item["response"])
            res_data["cached"] = True
            return res_data

    # 2. 存取併發佇列鎖定 (Semaphore)
    async with query_semaphore:
        # 檢索向量資料庫
        retrieved_chunks = vector_store.query_kb(query_text=query_text, top_k=req.top_k)
        
        if not retrieved_chunks:
            return {
                "answer": "抱歉，知識庫中未找到與您提問相關的 IBM FlashSystem 技術資料。",
                "sources": [],
                "cached": False
            }

        # 構建 Prompt 上下文
        context_str = ""
        sources_list = []

        for idx, item in enumerate(retrieved_chunks, 1):
            meta = item["metadata"]
            score = item["similarity_score"]
            content = item["content"]
            source = meta.get("source", "未知來源")
            page = meta.get("page", 1)
            item_type = meta.get("type", "text")
            image_path = meta.get("image_path", "")

            source_info = {
                "id": idx,
                "source": source,
                "page": page,
                "type": item_type,
                "score": score,
                "image_path": image_path
            }
            sources_list.append(source_info)

            context_str += f"[{idx}] 來源: {source} (第 {page} 頁, 類型: {item_type})\n{content}\n\n"

        # 呼叫 Ollama 生成專業解答
        prompt = (
            f"你是一位精通 IBM FlashSystem 儲存架構與紅皮書的資深技術專家。\n"
            f"請依據以下檢索到的官方技術資料，回答使用者的問題。\n"
            f"回答要求：\n"
            f"1. 請使用精準、專業的【繁體中文】回答。\n"
            f"2. 引用參考資料時請註明來源檔名與頁碼（例如：[來源: sg248520, 第 45 頁]）。\n"
            f"3. 若資料中提及技術圖表摘要，請明確指出可參考圖表。\n\n"
            f"【參考技術資料】：\n{context_str}\n"
            f"【使用者提問】：{query_text}\n\n"
            f"【專家解答】：\n"
        )

        answer_text = ""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{config.OLLAMA_HOST}/api/generate",
                    json={"model": config.LLM_MODEL, "prompt": prompt, "stream": False}
                )
                if resp.status_code == 200:
                    answer_text = resp.json().get("response", "").strip()
        except Exception as e:
            print(f"[警告] 呼叫 LLM 服務失敗或逾時: {e}")

        # 降級方案 (若 LLM 服務異常，直接回傳最相關段落)
        if not answer_text:
            answer_text = "【系統通知】LLM 推理服務暫時繁忙，以下為為您檢索出的最相關技術文檔段落：\n\n" + context_str

        response_payload = {
            "answer": answer_text,
            "sources": sources_list,
            "chunks_count": len(retrieved_chunks),
            "cached": False
        }

        # 寫入快取
        QUERY_CACHE[cache_key] = {
            "response": response_payload,
            "timestamp": now
        }

        return response_payload

@app.get("/api/images/{image_path:path}")
async def serve_extracted_image(image_path: str):
    """
    提供技術圖表圖片下載與預覽（包含防範 Path Traversal 安全檢驗）
    """
    target_path = Path(image_path)
    if not target_path.is_absolute():
        target_path = config.BASE_DIR / image_path

    resolved_path = target_path.resolve()

    # 安全防護規格 (Guardrail Spec): 檢查請求路徑是否屬於合法圖片目錄，防止讀取本機敏感檔案
    is_safe = False
    for allowed_dir in [config.LOCAL_DATA_DIR.resolve(), config.BASE_DIR.resolve()]:
        try:
            if resolved_path.is_relative_to(allowed_dir):
                is_safe = True
                break
        except Exception:
            pass

    if not is_safe or not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=403, detail="存取拒絕：非法圖片存取路徑")

    return FileResponse(resolved_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app:app", host=config.SERVER_HOST, port=config.PORTAL_PORT, reload=False)
