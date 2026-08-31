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

def is_test_query_turn(turn):
    q = turn['user_text'].lower()
    test_indicators = [
        '我的客戶想從傳統的gmcv',
        '請給我一個pbha ip quorum',
        '請幫我找出fs7300',
        'fs5200 sas adapter是額外插卡',
        '可以幫我查一下這個料件',
        '客戶原本使用 flashsystem 5200 hyperswap'
    ]
    if any(k in q for k in test_indicators):
        return True
    if q.startswith('@search_flashsystem_db') or q.startswith('@research_flashsystem_db'):
        return True
    return False

dev_turns = []
test_turns = []

for idx, turn in enumerate(turns, 1):
    turn['index'] = idx
    if is_test_query_turn(turn):
        test_turns.append(turn)
    else:
        dev_turns.append(turn)

# 1. 產生 docs/conversation_development_history.md
lines_dev = [
    '# IBM FlashSystem 專家系統 - 核心專案開發與架構對話紀錄 (Development Transcript)\n\n',
    '> **說明**：本文件完整記錄本專案之全流程架構討論、功能需求制定、Guardrail 防護體系、Cloudflare 穿透、防臆測引擎、動態數據修復與前端 PDF/圖片功能實作歷程（已自動剔除知識庫特定測試問答，以大幅節省 Context Window）。\n\n',
    '---\n\n'
]

for t in dev_turns:
    lines_dev.append(f"## 💬 對話輪次 #{t['index']}\n\n")
    if t['timestamp']:
        lines_dev.append(f"* **時間戳記**: `{t['timestamp']}`\n")
    lines_dev.append(f"### 👤 使用者指令 (User Request)\n\n{t['user_text']}\n\n")
    if t['tool_actions']:
        lines_dev.append("* **執行操作**: " + ", ".join(t['tool_actions'][:8]) + "\n\n")
    lines_dev.append("### 🤖 助手回覆 (Agent Response)\n\n")
    ans = "\n\n".join(t['assistant_responses']) if t['assistant_responses'] else "*(此輪次執行了工具調用並完成背景狀態更新)*"
    lines_dev.append(f"{ans}\n\n---\n\n")

with open('docs/conversation_development_history.md', 'w', encoding='utf-8') as f:
    f.writelines(lines_dev)

# 2. 產生 docs/conversation_test_queries_and_responses.md
lines_test = [
    '# IBM FlashSystem 知識庫 - 專案測試提問與輸出紀錄彙整 (Test Queries & Outputs)\n\n',
    '> **說明**：本文件完整收錄專案在開發與驗證期間所進行的所有「FlashSystem 知識庫技術測試問題、大模型回答、來源切片引述與比對結果」，作為未來模型準確度、防臆測 (Anti-Hallucination) 與回答一致性驗證的黃金測試集 (Golden Test Suite)。\n\n',
    '---\n\n'
]

for t in test_turns:
    lines_test.append(f"## 🧪 測試案例 #{t['index']}\n\n")
    if t['timestamp']:
        lines_test.append(f"* **測試時間**: `{t['timestamp']}`\n")
    lines_test.append(f"### ❓ 測試提問 (Test Query)\n\n```text\n{t['user_text']}\n```\n\n")
    lines_test.append("### 💡 專家系統回答與輸出結果 (Generated Output)\n\n")
    ans = "\n\n".join(t['assistant_responses']) if t['assistant_responses'] else "*(無正文輸出)*"
    lines_test.append(f"{ans}\n\n---\n\n")

with open('docs/conversation_test_queries_and_responses.md', 'w', encoding='utf-8') as f:
    f.writelines(lines_test)

print('Export complete without any zsh escaping issues!')
