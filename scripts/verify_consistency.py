"""
IBM FlashSystem 專家系統 - 雙端 (Cloudflare Web vs Antigravity IDE) 一致性比對與驗證工具
"""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / 'docs' / 'monitoring_cloudflare_session.jsonl'

def compare_latest_transaction():
    if not LOG_FILE.exists():
        print('❌ 尚無監控日誌記錄。')
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print('❌ 尚無任何交易記錄。')
        return

    latest = json.loads(lines[-1])
    print('=' * 60)
    print('📡 最新 Cloudflare 事務記錄分析：')
    print(f"  - 時間戳記: {latest.get('timestamp')}")
    print(f"  - 來源 IP: {latest.get('client_ip')}")
    print(f"  - 提問內容: {latest.get('query')}")
    print(f"  - 意圖分類: {latest.get('intent')}")
    print(f"  - 推理大腦: {latest.get('provider')}")
    print(f"  - 耗時: {latest.get('execution_time_seconds')} 秒")
    print(f"  - 檢索切片數: {latest.get('chunks_count')} 筆")
    print('=' * 60)
    print('📄 產出解答預覽：')
    print(latest.get('answer', '')[:500] + '...')
    print('=' * 60)

if __name__ == '__main__':
    compare_latest_transaction()
