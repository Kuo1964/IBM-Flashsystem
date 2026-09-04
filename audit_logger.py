# -*- coding: utf-8 -*-
"""
Audit Trail Engine - 全量對話審計與會話儲存引擎
負責：
1. 儲存全量問答日誌 (包含官方引用 Sources JSON, Token, 費用估算, 耗時)
2. 管理使用者的多對話主題 (Sessions)
3. 提供歷史主題調閱、匯出與刪除功能
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import config

DB_PATH = config.BASE_DIR / "storage_audit.db"

# Google Gemini Flash 費率標準 (USD / 1M Tokens)
INPUT_COST_PER_MILLION = 0.075
OUTPUT_COST_PER_MILLION = 0.300
USD_TO_TWD_RATE = 32.0

def init_audit_db():
    """初始化審計資料庫表"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # 1. 對話會話表
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    
    # 2. 問答審計日誌表
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        query_text TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        sources_json TEXT,
        tokens_input INTEGER DEFAULT 0,
        tokens_output INTEGER DEFAULT 0,
        tokens_total INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        cost_twd REAL DEFAULT 0.0,
        response_time_seconds REAL DEFAULT 0.0,
        provider TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    conn.commit()
    conn.close()

def estimate_tokens_and_cost(query_text: str, answer_text: str, context_str: str = "") -> Dict[str, Any]:
    """估算 Token 消耗量與相應費用 (USD / TWD)"""
    # 粗估：中文/英文混合每 1.5 ~ 2 個字元約為 1 Token
    in_tokens = int((len(query_text) + len(context_str) + 1000) / 1.8)
    out_tokens = int(len(answer_text) / 1.8)
    total_tokens = in_tokens + out_tokens
    
    cost_usd = (in_tokens / 1_000_000.0 * INPUT_COST_PER_MILLION) + (out_tokens / 1_000_000.0 * OUTPUT_COST_PER_MILLION)
    cost_twd = cost_usd * USD_TO_TWD_RATE
    
    return {
        "tokens_input": in_tokens,
        "tokens_output": out_tokens,
        "tokens_total": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "cost_twd": round(cost_twd, 4)
    }

def log_conversation_turn(
    user_id: int,
    session_id: str,
    query_text: str,
    answer_text: str,
    sources: List[Dict[str, Any]] = None,
    context_str: str = "",
    response_time_seconds: float = 0.0,
    provider: str = ""
) -> int:
    """記錄單次問答日誌，自動維護會話主題標題"""
    init_audit_db()
    cost_info = estimate_tokens_and_cost(query_text, answer_text, context_str)
    sources_json = json.dumps(sources or [], ensure_ascii=False)
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # 確保 session 存在
    c.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
    if not c.fetchone():
        # 自動截取第 1 題前 24 字作為主題標題
        title = query_text.strip().replace("\n", " ")
        if len(title) > 24:
            title = title[:24] + "..."
        c.execute(
            "INSERT INTO sessions (session_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (session_id, user_id, title)
        )
    else:
        c.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
        
    c.execute("""
    INSERT INTO chat_audit_logs (
        session_id, user_id, query_text, answer_text, sources_json,
        tokens_input, tokens_output, tokens_total, cost_usd, cost_twd,
        response_time_seconds, provider, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        session_id, user_id, query_text, answer_text, sources_json,
        cost_info["tokens_input"], cost_info["tokens_output"], cost_info["tokens_total"],
        cost_info["cost_usd"], cost_info["cost_twd"],
        response_time_seconds, provider
    ))
    log_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return log_id

def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """取得指定使用者的所有歷史會話主題列表"""
    init_audit_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
    SELECT s.session_id, s.title, s.created_at, s.updated_at, COUNT(l.log_id) as msg_count
    FROM sessions s
    LEFT JOIN chat_audit_logs l ON s.session_id = l.session_id
    WHERE s.user_id = ?
    GROUP BY s.session_id
    ORDER BY s.updated_at DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    
    return [
        {
            "session_id": r[0],
            "title": r[1],
            "created_at": r[2],
            "updated_at": r[3],
            "message_count": r[4]
        }
        for r in rows
    ]

def get_session_messages(session_id: str, user_id: int) -> List[Dict[str, Any]]:
    """取得指定會話的所有問答歷史訊息"""
    init_audit_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
    SELECT log_id, query_text, answer_text, sources_json, cost_twd, response_time_seconds, created_at
    FROM chat_audit_logs
    WHERE session_id = ? AND user_id = ?
    ORDER BY log_id ASC
    """, (session_id, user_id))
    rows = c.fetchall()
    conn.close()
    
    messages = []
    for r in rows:
        sources = []
        try:
            if r[3]:
                sources = json.loads(r[3])
        except Exception:
            pass
            
        messages.append({
            "log_id": r[0],
            "query": r[1],
            "answer": r[2],
            "sources": sources,
            "cost_twd": r[4],
            "response_time": r[5],
            "timestamp": r[6]
        })
    return messages

def delete_user_session(session_id: str, user_id: int) -> bool:
    """刪除指定會話及其所有日誌"""
    init_audit_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("DELETE FROM chat_audit_logs WHERE session_id = ? AND user_id = ?", (session_id, user_id))
    c.execute("DELETE FROM sessions WHERE session_id = ? AND user_id = ?", (session_id, user_id))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0
