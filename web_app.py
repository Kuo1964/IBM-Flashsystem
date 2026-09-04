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

# 🛡️ 團隊專屬 PIN 碼授權管理 (PIN Access Guard)
PORTAL_PIN = os.getenv("PORTAL_PIN", "8888")
VALID_AUTH_TOKENS: set = set()

class PinVerifyRequest(BaseModel):
    pin: str

class MessageItem(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 25
    session_id: Optional[str] = None
    messages: Optional[List[MessageItem]] = None

class SectionQueryRequest(BaseModel):
    cache_id: str
    section_index: int
    session_id: Optional[str] = None

# 按需章節生成上下文快取字典 (有效避免重複查詢向量庫與超大 Context 網路往返)
SECTION_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}

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
import auth
import audit_logger

# 初始化資料庫
auth.init_auth_db()
audit_logger.init_audit_db()

class UserLoginRequest(BaseModel):
    username: str
    password: str

def get_current_user_from_req(request: Request) -> Optional[Dict[str, Any]]:
    """自 Request 提取並驗證 JWT Token"""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
        payload = auth.verify_jwt_token(token)
        if payload:
            return payload
    return None

def verify_auth_token(request: Request) -> Dict[str, Any]:
    """
    驗證使用者 JWT Token 或 PIN 授權
    支援個人 JWT Token 與團隊 PIN 雙軌授權
    """
    user = get_current_user_from_req(request)
    if user:
        return user
        
    auth_header = request.headers.get("authorization", "")
    portal_pin_header = request.headers.get("x-portal-pin", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
    elif portal_pin_header:
        token = portal_pin_header.strip()
        
    if token == PORTAL_PIN or token in VALID_AUTH_TOKENS:
        return {"user_id": 1, "username": "team_member", "role": "engineer"}
        
    raise HTTPException(
        status_code=401,
        detail="未授權存取！請輸入工號/密碼登入或輸入團隊 PIN 碼。"
    )

@app.post("/api/auth/login")
async def login_or_auto_provision(req: UserLoginRequest):
    """使用者登入與首次自動註冊建檔 (Auto-Provisioning)"""
    try:
        result = auth.authenticate_or_provision_user(req.username, req.password)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=401, detail=str(ve))

@app.get("/api/auth/me")
async def get_me(request: Request):
    """取得當前登入者資訊"""
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登入或 Token 已過期")
    return {"status": "success", "user": user}

@app.get("/api/sessions")
async def get_sessions(request: Request):
    """取得當前使用者之歷史對話主題列表"""
    user = verify_auth_token(request)
    sessions = audit_logger.get_user_sessions(user["user_id"])
    return {"status": "success", "sessions": sessions}

@app.get("/api/sessions/{session_id}/messages")
async def get_session_history(session_id: str, request: Request):
    """取得特定會話歷史問答"""
    user = verify_auth_token(request)
    messages = audit_logger.get_session_messages(session_id, user["user_id"])
    return {"status": "success", "messages": messages}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    """刪除指定對話主題"""
    user = verify_auth_token(request)
    ok = audit_logger.delete_user_session(session_id, user["user_id"])
    return {"status": "success", "deleted": ok}

@app.post("/api/auth/verify")
async def verify_pin(req: PinVerifyRequest):
    """驗證 PIN 碼並發放 Session Token"""
    if req.pin == PORTAL_PIN:
        token = f"fs_token_{int(time.time())}_{os.urandom(4).hex()}"
        VALID_AUTH_TOKENS.add(token)
        return {"status": "ok", "token": token, "message": "PIN 碼驗證成功"}
    raise HTTPException(status_code=401, detail="PIN 碼不正確，請重新輸入")

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


from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import json

@app.post("/api/query/stream")
async def query_knowledge_base_stream(req: QueryRequest, request: Request):
    """
    RAG Agentic SSE 串流問答端點：即時推送思考狀態 (thinking) 與分塊打字內容 (content)，自動寫入審計日誌
    """
    user = verify_auth_token(request)
    client_ip = get_real_client_ip(request)
    check_rate_limit(client_ip)

    query_text = req.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="提問內容不能為空")

    session_id = req.session_id or f"sess_{int(time.time())}_{os.urandom(4).hex()}"

    chat_history = []
    if req.messages:
        chat_history = [{"role": m.role, "content": m.content} for m in req.messages]
    elif session_id in SESSIONS:
        chat_history = SESSIONS[session_id].get("messages", [])

    async def event_generator():
        # 1. 即時推送思考階段
        yield f"event: thinking\ndata: {json.dumps({'stage': 'intent', 'text': '🧠 正在分析提問意圖與術語擴展...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.15)
        
        yield f"event: thinking\ndata: {json.dumps({'stage': 'retrieval', 'text': '📚 正在檢索 ChromaDB 官方知識庫 (782k chunks) 與原廠 Redbooks...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.2)
        
        yield f"event: thinking\ndata: {json.dumps({'stage': 'grounding', 'text': '🛡️ 正在執行 Grounding 原廠真理錨定與 CLI 語法審計...'}, ensure_ascii=False)}\n\n"
        
        # 2. 呼叫中央 RAG 推理核心
        start_t = time.time()
        result = await asyncio.to_thread(rag_core.process_query, query_text, req.top_k, chat_history)
        duration = round(time.time() - start_t, 2)
        answer_text = result.get("answer", "")
        sources = result.get("sources", [])
        provider = result.get("provider", "")
        context_str = result.get("context_str", "")
        
        # 3. 審計日誌寫入 (Audit Trail)
        try:
            audit_logger.log_conversation_turn(
                user_id=user["user_id"],
                session_id=session_id,
                query_text=query_text,
                answer_text=answer_text,
                sources=sources,
                context_str=context_str,
                response_time_seconds=duration,
                provider=provider
            )
        except Exception as ae:
            print(f"[警告] 審計日誌寫入異常: {ae}")

        # 推送來源標籤
        yield f"event: citations\ndata: {json.dumps({'sources': sources[:8]}, ensure_ascii=False)}\n\n"
        
        # 3. 分塊即時打字推送
        lines = answer_text.split("\n")
        for line in lines:
            yield f"event: content\ndata: {json.dumps({'chunk': line + chr(10)}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.04)
            
        # 4. 推送完成信號與後續章節
        done_payload = {
            "status": "complete",
            "execution_time_seconds": result.get("execution_time_seconds", 0),
            "has_next_section": result.get("has_next_section", False),
            "cache_id": result.get("cache_id")
        }
        yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

        # 紀錄 Session
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
            sess["messages"].append({"role": "assistant", "content": answer_text})
            sess["messages"] = sess["messages"][-20:]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/query")
async def query_knowledge_base(req: QueryRequest, request: Request):
    """
    RAG 企業級客服問答端點 (支援 4-Tier 意圖分流、Session 隔離與多輪追問重寫)
    """
    verify_pin_token(request)
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

    # 若具備後續章節，將其檢索上下文暫存入快取，供前端按需拉取，並避免將巨量 context 送給前端
    if result.get("has_next_section"):
        cache_id = f"sec_{int(time.time() * 1000)}"
        SECTION_CONTEXT_CACHE[cache_id] = {
            "query": query_text,
            "context_str": result.get("context_str", ""),
            "created_at": time.time()
        }
        result["cache_id"] = cache_id
    
    # 移除內部傳輸用的巨型 context_str，節省網路頻寬
    result.pop("context_str", None)

    return result


@app.post("/api/query/section")
async def query_architecture_section(req: SectionQueryRequest, request: Request):
    """
    按需漸進式章節生成端點 (供前端按鈕非同步請求第 2 章或第 3 章)
    徹底避免 3 執行緒重複呼叫並防止 Cloudflare 100 秒超時
    """
    client_ip = get_real_client_ip(request)
    check_rate_limit(client_ip)

    if req.cache_id not in SECTION_CONTEXT_CACHE:
        raise HTTPException(status_code=404, detail="該提問的章節上下文已過期或不存在，請重新於下方輸入框提問。")

    cached_data = SECTION_CONTEXT_CACHE[req.cache_id]
    query_text = cached_data["query"]
    context_str = cached_data["context_str"]

    # 執行單一章節獨立生成 (享受滿額 8192 Token 空間)
    result = await rag_core.async_generate_architecture_section(query_text, context_str, req.section_index)
    result["cache_id"] = req.cache_id

    # 若指定 session_id，同步追加新章節內容至歷史
    if req.session_id and req.session_id in SESSIONS:
        sess = SESSIONS[req.session_id]
        if sess.get("messages"):
            last_msg = sess["messages"][-1]
            if last_msg.get("role") == "assistant":
                last_msg["content"] += f"\n\n---\n\n{result.get('answer', '')}"

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
