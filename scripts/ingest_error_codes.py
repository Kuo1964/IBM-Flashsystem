import zipfile
import re
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DATA_DIR = Path.home() / ".ibm_flashsystem_kb"
DB_PATH = LOCAL_DATA_DIR / "error_codes.sqlite3"
ZIP_PATH = LOCAL_DATA_DIR / "fs9x00.zip"

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS error_codes (
        code TEXT PRIMARY KEY,
        title TEXT,
        explanation TEXT,
        user_response TEXT,
        source_file TEXT,
        raw_text TEXT
    );
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_code ON error_codes (code);")
    conn.commit()
    conn.close()

def parse_and_insert_zip():
    if not ZIP_PATH.exists():
        print(f"❌ ZIP 檔案 {ZIP_PATH} 不存在！")
        return

    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    count = 0
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for fname in z.namelist():
            fname_lower = fname.lower()
            if not fname_lower.endswith(('.html', '.htm', '.xml')):
                continue
            if 'cmmvc' not in fname_lower and 'message' not in fname_lower and 'error' not in fname_lower:
                continue

            try:
                raw_content = z.read(fname).decode('utf-8', errors='ignore')
                soup = BeautifulSoup(raw_content, 'html.parser')
                
                text = soup.get_text()
                match = re.search(r'(CMMVC\d{4,5}[EWIS])', text, re.IGNORECASE)
                if not match:
                    match = re.search(r'(cmmvc\d{4,5}[ewis])', fname_lower)
                
                if match:
                    code = match.group(1).upper()
                    title = ""
                    h1 = soup.find(['h1', 'h2', 'title'])
                    if h1:
                        title = h1.get_text().strip()
                    
                    explanation = ""
                    user_response = ""
                    
                    for h in soup.find_all(['h2', 'h3', 'h4', 'section', 'div', 'p', 'b', 'strong']):
                        htext = h.get_text().strip()
                        if 'explanation' in htext.lower():
                            next_elem = h.find_next_sibling()
                            if next_elem:
                                explanation = next_elem.get_text().strip()
                        elif 'user response' in htext.lower() or 'response' in htext.lower():
                            next_elem = h.find_next_sibling()
                            if next_elem:
                                user_response = next_elem.get_text().strip()
                                
                    if not explanation:
                        exp_m = re.search(r'Explanation\s*[:\n]+(.*?)(?=User response|\Z)', text, re.DOTALL | re.IGNORECASE)
                        if exp_m:
                            explanation = exp_m.group(1).strip()
                            
                    if not user_response:
                        resp_m = re.search(r'User response\s*[:\n]+(.*?)(?=Related reference|\Z)', text, re.DOTALL | re.IGNORECASE)
                        if resp_m:
                            user_response = resp_m.group(1).strip()

                    c.execute("""
                    INSERT OR REPLACE INTO error_codes (code, title, explanation, user_response, source_file, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (code, title or code, explanation, user_response, fname, text[:1500]))
                    count += 1
            except Exception as e:
                continue

    conn.commit()
    conn.close()
    print(f"✅ 成功提取並注入 {count} 筆官方錯誤碼定義至 SQLite 資源組 ({DB_PATH})！")

def lookup_error_code(code: str) -> dict:
    """快速查找特定錯誤碼"""
    if not DB_PATH.exists():
        return None
    code_clean = code.strip().upper()
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT code, title, explanation, user_response, raw_text FROM error_codes WHERE code = ?", (code_clean,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "code": row[0],
                "title": row[1],
                "explanation": row[2],
                "user_response": row[3],
                "raw_text": row[4]
            }
    except Exception as e:
        print(f"[警告] 錯誤碼查詢異常: {e}")
    return None

if __name__ == "__main__":
    parse_and_insert_zip()
