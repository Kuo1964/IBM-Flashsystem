# -*- coding: utf-8 -*-
"""
Auto-Provisioning 使用者認證與 JWT 授權管理模組
支援：
1. PBKDF2-HMAC-SHA256 安全密碼雜湊與加鹽
2. 首次登入自動建檔 (Auto-Provisioning: 若同仁首次登入則自動於 SQLite 建立帳號並開闢獨立會話空間)
3. JWT Token 簽署與解析中介層
"""

import os
import time
import json
import base64
import hmac
import hashlib
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import config

DB_PATH = config.BASE_DIR / "storage_audit.db"
JWT_SECRET = os.getenv("JWT_SECRET", "flashsystem-expert-jwt-secret-key-2026")
JWT_EXPIRE_SECONDS = 86400 * 30  # 30 天有效期

security = HTTPBearer(auto_error=False)

def init_auth_db():
    """初始化使用者與認證資料表"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'engineer',
        display_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """使用 PBKDF2-HMAC-SHA256 進行密碼加鹽雜湊"""
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    hash_str = base64.b64encode(dk).decode('utf-8')
    return f"{salt}${hash_str}"

def verify_password(password: str, stored_hash: str) -> bool:
    """驗證密碼"""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 2:
            return False
        salt, _ = parts
        return hash_password(password, salt) == stored_hash
    except Exception:
        return False

def generate_jwt_token(payload: Dict[str, Any]) -> str:
    """生成輕量安全 JWT Token (HMAC-SHA256)"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = payload.copy()
    payload["exp"] = int(time.time()) + JWT_EXPIRE_SECONDS
    payload["iat"] = int(time.time())

    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{s_b64}"

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """驗證 JWT Token 簽名與過期時間"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_b64, p_b64, s_b64 = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
        
        # 補回 base64 padding
        rem = len(s_b64) % 4
        if rem > 0:
            s_b64 += "=" * (4 - rem)
        actual_sig = base64.urlsafe_b64decode(s_b64.encode())
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        rem_p = len(p_b64) % 4
        if rem_p > 0:
            p_b64 += "=" * (4 - rem_p)
        payload = json.loads(base64.urlsafe_b64decode(p_b64.encode()).decode())
        
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def authenticate_or_provision_user(username: str, password: str) -> Dict[str, Any]:
    """
    登入或首次自動註冊建檔 (Auto-Provisioning)
    - 若使用者存在：校驗密碼
    - 若使用者不存在：自動為其建立帳號並開闢獨立空間
    """
    init_auth_db()
    username = username.strip()
    if not username or not password:
        raise ValueError("使用者名稱與密碼不可為空")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT user_id, username, password_hash, role, display_name FROM users WHERE username = ?", (username,))
    row = c.fetchone()

    if row:
        user_id, uname, p_hash, role, d_name = row
        if not verify_password(password, p_hash):
            conn.close()
            raise ValueError("密碼不正確")
        c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        conn.commit()
    else:
        # 首次自動建檔 (Auto-Provisioning)
        p_hash = hash_password(password)
        role = "admin" if username.lower() in ["admin", "johnkuo"] else "engineer"
        d_name = username
        c.execute(
            "INSERT INTO users (username, password_hash, role, display_name, last_login) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (username, p_hash, role, d_name)
        )
        user_id = c.lastrowid
        conn.commit()
        print(f"[Auto-Provisioning] 已為新同仁 '{username}' 自動建立專屬帳號與會話空間！")

    conn.close()

    token = generate_jwt_token({
        "user_id": user_id,
        "username": username,
        "role": role,
        "display_name": d_name or username
    })

    return {
        "status": "success",
        "token": token,
        "user": {
            "user_id": user_id,
            "username": username,
            "role": role,
            "display_name": d_name or username
        }
    }

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    """FastAPI 依賴注入：驗證 Token 並取得當前使用者"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供身份驗證憑證")
    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="無效或已過期的身份憑證")
    return payload
