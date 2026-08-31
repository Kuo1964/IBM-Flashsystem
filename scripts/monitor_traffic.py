"""
IBM FlashSystem 專家系統 - Cloudflare 公網請求全流程即時監控與日誌記錄器
"""
import time
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / 'docs' / 'monitoring_cloudflare_session.jsonl'

def log_transaction(payload: dict):
    record = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        'epoch': time.time(),
        **payload
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"📡 [監控器] 已成功記錄一筆請求事務 (提問: '{payload.get('query', '')[:25]}...')")

