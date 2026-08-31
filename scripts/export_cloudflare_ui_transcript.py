import json
import re
from pathlib import Path

transcript_path = Path('/Users/johnkuo/.gemini/antigravity/brain/7428dfab-6cee-4f61-84a3-a1361d00ae9a/.system_generated/logs/transcript_full.jsonl')
if not transcript_path.exists():
    transcript_path = Path('/Users/johnkuo/.gemini/antigravity/brain/7428dfab-6cee-4f61-84a3-a1361d00ae9a/.system_generated/logs/transcript.jsonl')

steps = []
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                steps.append(json.loads(line))
            except Exception:
                pass

turns = []
current_turn = None

for step in steps:
    stype = step.get('type')
    source = step.get('source')
    content = step.get('content', '')
    ts = step.get('timestamp', '')
    
    if stype == 'USER_INPUT' and source == 'USER_EXPLICIT':
        if current_turn:
            turns.append(current_turn)
        
        text = content
        if isinstance(content, dict):
            text = content.get('text', '')
            
        match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
        else:
            clean_text = text.strip()
            
        current_turn = {
            'user_text': clean_text,
            'timestamp': ts,
            'assistant_responses': [],
            'tool_actions': []
        }
    elif current_turn:
        if stype == 'PLANNER_RESPONSE':
            if isinstance(content, str) and content.strip():
                current_turn['assistant_responses'].append(content.strip())
            elif isinstance(content, dict) and 'text' in content:
                current_turn['assistant_responses'].append(content['text'].strip())
        
        tool_calls = step.get('tool_calls', [])
        for tc in tool_calls:
            fn = tc.get('function', {}).get('name', '')
            args = tc.get('function', {}).get('arguments', {})
            act = args.get('toolAction', '') or args.get('toolSummary', '')
            if act and act not in current_turn['tool_actions']:
                current_turn['tool_actions'].append(f'{fn}: {act}')

if current_turn:
    turns.append(current_turn)

# 篩選條件：僅針對 Cloudflare 網頁入口、Web Portal、前端 UI/UX 設計、深色主題、PDF 匯出、圖片顯示、網址固定等對話
ui_keywords = [
    'cloudflare', 'web', 'ui', '網頁', '入口', '介面', '靜態網址', '固定網址', '網址',
    'domain', '域名', '圖片', '顯示圖片', 'pdf', '匯出', 'service desk', 'portal',
    'index.html', '前端', '側邊欄', '深色模式', 'css', '按鈕', '對話框', '氣泡', '截斷',
    '伺服器回應異常', '49 本', '72,748', '動態統計'
]

def is_cloudflare_ui_turn(turn):
    q = turn['user_text'].lower()
    combined_ans = ' '.join(turn['assistant_responses']).lower()
    
    # Check if user explicitly talked about cloudflare, web ui, pdf, images, domain, etc.
    if any(k in q for k in ['cloudflare', '網頁', 'ui', '介面', '網址', 'domain', '域名', 'pdf', '圖片', '匯出', '截斷', '伺服器回應異常', '固定', '49 本', '72,748']):
        return True
    if any(k in combined_ans for k in ['cloudflare', 'trycloudflare', 'web portal', 'static/index.html', 'exporttopdf', 'serve_extracted_image']):
        # If user asked a web portal question
        if 'ui' in q or '網頁' in q or 'cloudflare' in q or '圖' in q or 'pdf' in q or '網址' in q:
            return True
    return False

cloudflare_ui_turns = []
for idx, turn in enumerate(turns, 1):
    turn['index'] = idx
    if is_cloudflare_ui_turn(turn):
        cloudflare_ui_turns.append(turn)

lines = [
    '# IBM FlashSystem 專家系統 - Cloudflare 網頁入口與 UI 介面設計專屬對話紀錄\n\n',
    '> **說明**：本文件專門聚焦並收錄與 **Cloudflare 穿透、Web Portal 前端 UI/UX 設計、深色主題、防截斷修復、動態知識庫統計、實體技術圖表串流渲染與 PDF 報告一鍵匯出** 等相關的完整對話歷程、設計決策與實施步驟。\n\n',
    '---\n\n'
]

for t in cloudflare_ui_turns:
    lines.append(f"## 🌐 UI/Cloudflare 對話輪次 #{t['index']}\n\n")
    if t['timestamp']:
        lines.append(f"* **時間戳記**: `{t['timestamp']}`\n")
    lines.append(f"### 👤 使用者需求與反饋 (User Request)\n\n{t['user_text']}\n\n")
    if t['tool_actions']:
        lines.append("* **執行操作**: " + ", ".join(t['tool_actions'][:8]) + "\n\n")
    lines.append("### 🎨 介面與架構實作回覆 (Agent Response)\n\n")
    ans = "\n\n".join(t['assistant_responses']) if t['assistant_responses'] else "*(已完成相關代碼調整與伺服器重啟)*"
    lines.append(f"{ans}\n\n---\n\n")

with open('docs/conversation_cloudflare_web_ui_design.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Done! Exported {len(cloudflare_ui_turns)} Cloudflare/UI turns to docs/conversation_cloudflare_web_ui_design.md')
