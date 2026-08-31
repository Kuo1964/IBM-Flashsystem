# Implementation Plan - IBM FlashSystem 雲端問答入口 (Web Portal) 連線中斷 Bug 診斷與常駐守護架構升級計畫

**建立時間**: `2026-08-17 16:09:31`  
**分支名稱**: `feature/rag-quality-upgrade`  
**核心目標**: 徹底定位並修復「❌ 網路連線錯誤，請確認 Web Portal 服務已啟動」之連線中斷 Bug，建立通用型 **OS Session Leader 獨立常駐守護腳本 (Daemon Runner)** 與健康檢測端點，確保 Web 服務與 Cloudflare 通道 100% 永續穩定在線。

---

## 🔍 Bug 診斷報告與 Codebase Recon (Diagnosis & Recon)

### 1. 斷線 Bug 根因定位 (Root Cause Analysis)
* **現象**：使用者在 Web 網頁點擊查詢時，彈出 `❌ 網路連線錯誤，請確認 Web Portal 服務已啟動`，且 `http://localhost:8888` 無法連線（Cloudflare 回傳 HTTP 502 Bad Gateway）。
* **機制根因**：
  * 先前背景啟動 `web_app.py` 與 `cloudflared` 時，屬於 Agent 子 Shell 關聯進程。
  * 當 Agent 的單次對話任務完成或背景 Task 被系統收回時，子 Shell 會自動向所有附屬進程發送 `SIGHUP` 訊號，導致 `web_app.py` 進程非預期退出。
* **驗證驗證**：
  * 在子 Shell 中使用 `start_new_session=True` 建立獨立 Session Group 後，進程成功提升為 OS Session Leader (狀態: `Ss`)，成功完全脫離 Shell 生命週期，徹底擺脫 SIGHUP 訊號干擾！

---

## 🛡️ Guardrail Spec (系統護城河規範)

修改過程必須嚴格遵守以下 **5 大 Guardrail 規範**：

1. **進程隔離與持久性 Guardrail (Process Isolation Guardrail)**：
   * 所有網頁與隧道守護進程必須使用 `start_new_session=True`，確保 PID 完全獨立於任何 IDE / Shell / Terminal 生命週期。
2. **零阻斷降級 Guardrail (Zero-Downtime Fallback Guardrail)**：
   * 腳本啟動前必須先自動清理舊的 8888 Port 殘留進程，防止 Port Binding Collision 衝突。
3. **路徑安全Guardrail (Path Safety Guardrail)**：
   * 保持 `web_app.py` 的絕對路徑存取防護 (`is_relative_to`) 規範。
4. **語言與日誌 Guardrail (Language Protocol Guardrail)**：
   * 思考過程、註解、計畫與系統通知**強制 100% 使用繁體中文**。
5. **審查與批准 Guardrail (Review Before Execution Guardrail)**：
   * **未獲得使用者明確審查批准前，停止所有應用程式與腳本修改動作**。

---

## 📝 Brownfield Diff Review (舊程式碼與擬修改程式碼對比)

### 1. 新增獨立一鍵常駐腳本 `scripts/start_portal_daemon.py` [NEW]

#### 🟢 擬新增程式碼 (Proposed New File):
```python
"""
IBM FlashSystem 專家系統 - 雲端入口持久化常駐進程啟動腳本
使用 start_new_session=True 將進程提升為 OS Session Leader，徹底防範 SIGHUP 斷線
"""
import os
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def main():
    print("🚀 正在啟動 IBM FlashSystem 雲端問答入口常駐守護進程...")
    
    # 1. 清理舊進程
    subprocess.run(["lsof -ti :8888 | xargs kill -9 2>/dev/null || true"], shell=True)
    subprocess.run(["pkill -9 cloudflared 2>/dev/null || true"], shell=True)
    time.sleep(1)

    # 2. 啟動 web_app.py 守護進程
    venv_python = BASE_DIR / ".venv" / "bin" / "python"
    web_log = open("/tmp/web_app_daemon.log", "a", encoding="utf-8")
    web_proc = subprocess.Popen(
        [str(venv_python), "web_app.py"],
        cwd=str(BASE_DIR),
        stdout=web_log,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    # 3. 啟動 cloudflared 加密隧道
    cf_log = open("/tmp/cloudflared_daemon.log", "a", encoding="utf-8")
    cf_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:8888"],
        cwd=str(BASE_DIR),
        stdout=cf_log,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    print(f"✅ 常駐守護進程已成功啟動！(Web PID: {web_proc.pid}, Cloudflare PID: {cf_proc.pid})")

if __name__ == "__main__":
    main()
```

---

### 2. `web_app.py` (新增 `/api/health` 探針端點)

#### 🔴 現有舊程式碼 (Before):
無 `/api/health` 探針端點。

#### 🟢 擬替換新程式碼 (Proposed After):
```python
@app.get("/api/health")
async def health_check():
    """健康度檢查探針端點"""
    return {"status": "ok", "timestamp": time.time(), "message": "IBM FlashSystem Web Portal 運作正常"}
```

---

## 🛠️ Proposed Changes (預計修改檔案總覽)

### [NEW] `scripts/start_portal_daemon.py`
* 實現脫離 Shell 的獨立常駐守護啟動器。

### [NEW] `scripts/stop_portal_daemon.py`
* 提供一鍵優雅關閉服務腳本。

### [MODIFY] [web_app.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/web_app.py)
* 新增 `/api/health` 探針端點供連線狀態即時檢測。

### [MODIFY] [wizard_cloud_setup.sh](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/IBM_Flashsystem/Knowledge_DB/wizard_cloud_setup.sh)
* 更新階段 4 調用 `scripts/start_portal_daemon.py`。

---

## 🧪 Verification Plan (驗證計畫)

### 1. 斷線防禦極限測試 (Disconnect Defense Test)
1. 執行 `python3 scripts/start_portal_daemon.py` 啟動服務。
2. 關閉啟動腳本終端機或終止上層 Shell。
3. 執行 `ps aux | grep web_app.py`，驗證進程 PID 是否依然維持為 `Ss` 狀態且 Port 8888 正常監聽。

### 2. 公網 HTTPS 連結實測 (Cloudflare Public URL Verification)
1. 從 `/tmp/cloudflared_daemon.log` 提取最新的 Cloudflare 加密網址。
2. 使用 `curl -s https://<subdomain>.trycloudflare.com/api/health` 驗證，確認回傳 `{"status": "ok"}`。
3. 在瀏覽器打開網址並發起測試提問，確認不再出現 `❌ 網路連線錯誤`。

---

## 🛑 User Review Required (等待使用者審查)

> [!IMPORTANT]
> **本 Implementation Plan 現已完整製作完畢。根據指令，我已停止所有修改動作，等待您的審查與批准。批准後即可開始執行！**
