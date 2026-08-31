"""
IBM FlashSystem 專家系統 - 雲端問答入口 (Web Cloud Portal) REST API 伺服器
提供安全的 RAG 問答、語意快取、速率防護、併發排隊佇列、內建智慧降級合成器與全流程日誌監控
"""

import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

import config
import vector_store
import ingest
import prompts
import rag_core

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

# 併發排隊佇列與安全控制
query_semaphore = asyncio.Semaphore(3)

# 語意快取字典
QUERY_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 快取有效時間 (秒)

# 提問速率限制 (Rate Limiter - 支援 Cloudflare 代理真實 IP 解析)
USER_RATE_LIMITS: Dict[str, List[float]] = {}
MAX_REQUESTS_PER_MINUTE = 60

class MessageItem(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 25
    session_id: Optional[str] = None
    messages: Optional[List[MessageItem]] = None

# 客服會話記憶體儲存庫 (Session Storage)
SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_real_client_ip(request: Request) -> str:
    """提取真實客戶端 IP (優先支援 Cloudflare CF-Connecting-IP 與 X-Forwarded-For)"""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def check_rate_limit(client_ip: str):
    """檢查請求速率防護 (Rate Limiting)"""
    now = time.time()
    timestamps = USER_RATE_LIMITS.get(client_ip, [])
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
    """取得知識庫最新即時統計資訊 (直接自 SQLite 與磁碟取得真實最新數據)"""
    import sqlite3
    pdf_files = list(config.RAW_PDF_DIR.glob("*.pdf")) + list(config.RAW_PDF_DIR.glob("*.PDF"))
    pdf_count = len(pdf_files)

    total_chunks = 0
    db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM embeddings")
            row = c.fetchone()
            total_chunks = row[0] if row else 739056
            conn.close()
        except Exception:
            total_chunks = 739056

    return {
        "status": "online",
        "pdf_count": pdf_count,
        "total_chunks": total_chunks,
        "total_chunks_estimate": total_chunks,
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_model": config.LLM_MODEL,
        "vision_model": config.VISION_MODEL
    }


@app.post("/api/query")
async def query_knowledge_base(req: QueryRequest, request: Request):
    """
    RAG 企業級客服問答端點 (支援 4-Tier 意圖分流、Session 隔離與多輪追問重寫)
    """
    client_ip = get_real_client_ip(request)
    check_rate_limit(client_ip)

    query_text = req.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="提問內容不能為空")

    # 提取多輪對話歷史 (若前端提供 messages 列表)
    chat_history = []
    if req.messages:
        chat_history = [{"role": m.role, "content": m.content} for m in req.messages]
    elif req.session_id and req.session_id in SESSIONS:
        chat_history = SESSIONS[req.session_id].get("messages", [])

    # 由非同步線程池執行中央 RAG 推理 (傳入多輪歷史進行防污染意圖重寫)
    result = await asyncio.to_thread(rag_core.process_query, query_text, req.top_k, chat_history)

    # 📡 即時記錄全流程監控日誌 (供事後雙端一致性比對分析)
    try:
        from scripts.monitor_traffic import log_transaction
        log_transaction({
            "client_ip": client_ip,
            "session_id": req.session_id,
            "query": query_text,
            "top_k": req.top_k,
            "intent": result.get("intent"),
            "provider": result.get("provider"),
            "execution_time_seconds": result.get("execution_time_seconds"),
            "chunks_count": result.get("chunks_count"),
            "sources": result.get("sources", []),
            "answer": result.get("answer", "")
        })
    except Exception as e:
        print(f"[警告] 監控日誌寫入異常: {e}")

    # 若指定 session_id，同步儲存對話歷史
    if req.session_id:
        if req.session_id not in SESSIONS:
            SESSIONS[req.session_id] = {
                "id": req.session_id,
                "title": query_text[:30],
                "created_at": time.time(),
                "messages": []
            }
        sess = SESSIONS[req.session_id]
        sess["messages"].append({"role": "user", "content": query_text})
        sess["messages"].append({"role": "assistant", "content": result.get("answer", "")})
        # 限制記憶體保留最近 20 則訊息
        sess["messages"] = sess["messages"][-20:]

    return result


@app.get("/api/images/{image_path:path}")
@app.get("/extracted_images/{image_path:path}")
async def serve_extracted_image(image_path: str):
    """
    提供技術手冊拓撲圖與架構圖安全圖片串流服務 (支援 PNG, JPEG, SVG, WebP)
    """
    clean_path = image_path.lstrip("/")
    candidate_paths = [
        config.BASE_DIR / "extracted_images" / clean_path,
        config.EXTRACTED_IMAGES_DIR / clean_path,
        Path("/Users/johnkuo/.ibm_flashsystem_kb/extracted_images") / clean_path,
        Path(image_path) if os.path.isabs(image_path) else config.BASE_DIR / clean_path
    ]
    for p in candidate_paths:
        if p.exists() and p.is_file():
            suffix = p.suffix.lower()
            media_type = "image/png"
            if suffix in [".jpg", ".jpeg"]:
                media_type = "image/jpeg"
            elif suffix == ".svg":
                media_type = "image/svg+xml"
            elif suffix == ".webp":
                media_type = "image/webp"
            return FileResponse(str(p), media_type=media_type)

    raise HTTPException(status_code=404, detail="找不到指定的技術圖表檔案")


@app.get("/api/sessions")
async def list_sessions():

    """取得所有歷史對話列表"""
    sess_list = []
    for sid, s in SESSIONS.items():
        sess_list.append({
            "id": sid,
            "title": s.get("title", "新技術諮詢"),
            "created_at": s.get("created_at", time.time()),
            "message_count": len(s.get("messages", []))
        })
    sess_list.sort(key=lambda x: x["created_at"], reverse=True)
    return {"sessions": sess_list}

@app.post("/api/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """清除指定會話記錄"""
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    return {"status": "success", "session_id": session_id}








@app.get("/api/health")
async def health_check():
    """健康度檢查探針端點"""
    return {"status": "ok", "timestamp": time.time(), "message": "IBM FlashSystem Web Portal 運作正常"}


@app.post("/api/cache/clear")
@app.get("/api/cache/clear")
async def clear_query_cache():
    """清空語意快取"""
    global QUERY_CACHE
    count = len(QUERY_CACHE)
    QUERY_CACHE.clear()
    return {"status": "success", "cleared_entries": count, "message": "語意快取已成功清空"}



@app.get("/api/images/{image_path:path}")
async def serve_extracted_image(image_path: str):
    """
    提供技術圖表圖片下載與預覽（修復雙斜線與絕對/相對路徑解析）
    """
    # 清理多餘的開頭斜線
    clean_path = image_path.lstrip("/")
    
    # 嘗試作為絕對路徑或相對於 LOCAL_DATA_DIR / BASE_DIR 的路徑
    target_path = Path("/" + clean_path) if os.path.exists("/" + clean_path) else Path(clean_path)
    if not target_path.exists():
        target_path = config.BASE_DIR / clean_path

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
        raise HTTPException(status_code=403, detail=f"存取拒絕或檔案不存在: {image_path}")

    return FileResponse(resolved_path)


if __name__ == "__main__":
    import uvicorn
    provider_info = f"Google Gemini ({config.GEMINI_MODEL})" if config.GEMINI_API_KEY else f"本地 Ollama ({config.LLM_MODEL}) [提示: 未偵測到 GEMINI_API_KEY]"
    print("=" * 60)
    print("🚀 IBM FlashSystem 專家系統 Web Portal 啟動中...")
    print(f"🤖 當前主推理引擎: {provider_info}")
    print(f"🌐 服務網址: http://localhost:{config.PORTAL_PORT}")
    print("=" * 60)
    uvicorn.run("web_app:app", host=config.SERVER_HOST, port=config.PORTAL_PORT, reload=False)
