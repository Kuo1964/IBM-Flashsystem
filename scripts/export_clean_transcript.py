"""
IBM FlashSystem 專家系統 - 完整對話記錄與測試日誌分離匯出腳本
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPT_PATH = Path('/Users/johnkuo/.gemini/antigravity/brain/7428dfab-6cee-4f61-84a3-a1361d00ae9a/.system_generated/logs/transcript.jsonl')
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

MAIN_MD_PATH = DOCS_DIR / "conversation_history_main.md"
TEST_MD_PATH = DOCS_DIR / "conversation_history_test_and_execution_logs.md"

def clean_user_text(text: str) -> str:
    text = re.sub(r'<USER_REQUEST>\s*', '', text)
    text = re.sub(r'</USER_REQUEST>', '', text)
    text = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', text)
    text = re.sub(r'<SYSTEM_MESSAGE>[\s\S]*?</SYSTEM_MESSAGE>', '', text)
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>', '', text)
    return text.strip()

def export_transcripts():
    if not TRANSCRIPT_PATH.exists():
        print(f"❌ 找不到 Transcript: {TRANSCRIPT_PATH}")
        return

    main_entries = []
    test_entries = []
    turn_idx = 1

    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                step_type = item.get("type")
                source = item.get("source")
                content = item.get("content", "")
                tool_calls = item.get("tool_calls", [])

                # 1. 使用者提問
                if step_type == "USER_INPUT" and source == "USER_EXPLICIT":
                    cleaned = clean_user_text(content)
                    if cleaned:
                        main_entries.append(f"\n\n---\n\n## 👤 對話輪次 {turn_idx}：使用者提問\n\n{cleaned}\n")
                        test_entries.append(f"\n\n---\n\n## 👤 對話輪次 {turn_idx}：使用者提問概要\n\n> {cleaned[:150]}...\n")
                        turn_idx += 1

                # 2. 助手回覆與工具調用
                elif step_type == "PLANNER_RESPONSE":
                    if content and content.strip():
                        if not content.startswith("Created At:") and not content.startswith("Task id"):
                            main_entries.append(f"\n### 🤖 助手回覆\n\n{content.strip()}\n")

                    if tool_calls:
                        for tc in tool_calls:
                            fn = tc.get("function", {})
                            fn_name = fn.get("name", "")
                            fn_args = fn.get("arguments", {})

                            if fn_name == "run_command":
                                cmd = fn_args.get("CommandLine", "")
                                test_entries.append(f"\n#### ⚙️ 執行指令: `{cmd}`\n")
                            elif fn_name == "view_file":
                                fpath = fn_args.get("AbsolutePath", "")
                                test_entries.append(f"- 📄 讀取檔案: `{fpath}`\n")
                            elif fn_name == "replace_file_content":
                                fpath = fn_args.get("TargetFile", "")
                                desc = fn_args.get("Description", "")
                                test_entries.append(f"- ✏️ 修改檔案: `{fpath}` ({desc})\n")
                            elif fn_name == "grep_search":
                                query = fn_args.get("Query", "")
                                test_entries.append(f"- 🔍 搜尋模式: `{query}`\n")

                # 3. 系統輸出 / 測試日誌
                elif step_type == "USER_INPUT" and source in ["SYSTEM", "MODEL"]:
                    if content and content.strip():
                        test_entries.append(f"\n```text\n{content.strip()[:3000]}\n```\n")

            except Exception:
                pass

    # 寫入純淨主對話記錄
    header_main = """# 📚 IBM FlashSystem 專家系統專案完整對話記錄（純淨核心版）

> **會話 ID**: `7428dfab-6cee-4f61-84a3-a1361d00ae9a`  
> **建立時間**: 2026-08-20  
> **說明**: 本文件收錄本專案從開案至今所有核心技術諮詢、架構設計決策、故障診斷分析、功能規範與原廠知識庫問答。已徹底剔除中途執行的終端命令、測試腳本與底層運行日誌，適合快速回溯專案脈絡與縮減 Context Window。

"""
    with open(MAIN_MD_PATH, "w", encoding="utf-8") as f:
        f.write(header_main + "".join(main_entries))

    # 寫入測試與指令日誌
    header_test = """# 🧪 IBM FlashSystem 專家系統專案測試執行與終端命令日誌（測試日誌專屬版）

> **會話 ID**: `7428dfab-6cee-4f61-84a3-a1361d00ae9a`  
> **建立時間**: 2026-08-20  
> **說明**: 本文件收錄在開發與調試過程中所執行的所有終端指令 (`run_command`)、單元測試 (`unittest`)、API 探測日誌、檔案修改軌跡與系統輸出結果。

"""
    with open(TEST_MD_PATH, "w", encoding="utf-8") as f:
        f.write(header_test + "".join(test_entries))

    print(f"✅ 主對話記錄已完成匯出: {MAIN_MD_PATH} ({MAIN_MD_PATH.stat().st_size:,} bytes)")
    print(f"✅ 測試日誌記錄已完成匯出: {TEST_MD_PATH} ({TEST_MD_PATH.stat().st_size:,} bytes)")

if __name__ == "__main__":
    export_transcripts()
