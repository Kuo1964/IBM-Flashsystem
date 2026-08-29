import zipfile
import re
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DATA_DIR = Path.home() / ".ibm_flashsystem_kb"
DB_PATH = LOCAL_DATA_DIR / "error_codes.sqlite3"
PACKAGES_DIR = LOCAL_DATA_DIR / "downloaded_packages"

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

def parse_and_insert_all_zips():
    zip_files = list(PACKAGES_DIR.glob("*.zip"))
    if not zip_files and (LOCAL_DATA_DIR / "fs9x00.zip").exists():
        zip_files = [LOCAL_DATA_DIR / "fs9x00.zip"]

    if not zip_files:
        print(f"❌ 找不到任何 ZIP 檔案！")
        return

    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    total_inserted = 0
    total_updated = 0

    print("=" * 70)
    print(f"🚀 正在掃描 {len(zip_files)} 個官方手冊包以提取全量錯誤代碼...")
    print("=" * 70)

    for zip_path in sorted(zip_files):
        print(f"📦 解析手冊包: {zip_path.name}...")
        count = 0
        with zipfile.ZipFile(zip_path, 'r') as z:
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
                        
                        # 提取 Explanation
                        exp_tag = soup.find(text=re.compile(r'Explanation', re.I))
                        if exp_tag and exp_tag.parent:
                            p = exp_tag.parent.find_next_sibling(['p', 'div', 'dd', 'section'])
                            if p:
                                explanation = p.get_text().strip()
                        if not explanation:
                            m_exp = re.search(r'Explanation:?\s*([\s\S]+?)(?:User response|Administrator response|\Z)', text, re.I)
                            if m_exp:
                                explanation = m_exp.group(1).strip()
                                
                        # 提取 User response
                        res_tag = soup.find(text=re.compile(r'User response|Administrator response', re.I))
                        if res_tag and res_tag.parent:
                            p = res_tag.parent.find_next_sibling(['p', 'div', 'dd', 'ol', 'ul', 'section'])
                            if p:
                                user_response = p.get_text().strip()
                        if not user_response:
                            m_res = re.search(r'(?:User response|Administrator response):?\s*([\s\S]+?)(?:\Z)', text, re.I)
                            if m_res:
                                user_response = m_res.group(1).strip()

                        raw_clean = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

                        c.execute("""
                        INSERT INTO error_codes (code, title, explanation, user_response, source_file, raw_text)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(code) DO UPDATE SET
                            title=excluded.title,
                            explanation=excluded.explanation,
                            user_response=excluded.user_response,
                            source_file=excluded.source_file,
                            raw_text=excluded.raw_text;
                        """, (code, title, explanation, user_response, f"{zip_path.name}:{fname}", raw_clean))
                        count += 1
                except Exception:
                    continue

        conn.commit()
        print(f"  ✅ {zip_path.name}: 處理 {count} 條錯誤代碼")
        total_inserted += count

    c.execute("SELECT COUNT(*) FROM error_codes;")
    total_unique = c.fetchone()[0]
    conn.close()

    print("\n" + "=" * 70)
    print(f"🎉 錯誤碼結構化字典庫更新完畢！")
    print(f"📚 總計唯一官方錯誤代碼數量: {total_unique} 條")
    print(f"💾 資料庫檔案路徑: {DB_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    parse_and_insert_all_zips()
