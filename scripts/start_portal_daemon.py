"""
IBM FlashSystem 專家系統 - 雲端入口持久化常駐進程啟動腳本
支援固定 Token 隧道、HTTP2/QUIC 連線加固、即時 URL 提取與斷線自癒
"""
import os
import sys
import time
import re
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def extract_active_url(log_path: str, max_wait: int = 15) -> str:
    """從 cloudflared 日誌中即時提取有效的 trycloudflare.com 網址"""
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    start = time.time()
    while time.time() - start < max_wait:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = url_pattern.findall(content)
                if matches:
                    return matches[-1]
        time.sleep(1)
    return ""

def main():
    print("=" * 60)
    print("🚀 正在啟動 IBM FlashSystem 雲端問答入口常駐守護進程...")
    print("=" * 60)
    
    # 1. 清理舊進程防止 Port 8888 衝突
    subprocess.run(["lsof -ti :8888 | xargs kill -9 2>/dev/null || true"], shell=True)
    subprocess.run(["pkill -9 cloudflared 2>/dev/null || true"], shell=True)
    time.sleep(1)

    # 2. 開啟 OS 級別檔案描述符 (防範 Python GC 導致 SIGPIPE)
    log_cf_path = "/tmp/cloudflared_daemon.log"
    # 清空或重置 log 開頭
    with open(log_cf_path, "w") as f:
        f.write(f"--- Cloudflare Tunnel Session Started at {time.ctime()} ---\n")

    fd_web = os.open("/tmp/web_app_daemon.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    fd_cf = os.open(log_cf_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

    # 3. 啟動 web_app.py 守護進程 (OS Session Leader)
    venv_python = BASE_DIR / ".venv" / "bin" / "python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
    
    web_proc = subprocess.Popen(
        [python_bin, "web_app.py"],
        cwd=str(BASE_DIR),
        stdout=fd_web,
        stderr=subprocess.STDOUT,
        close_fds=False,
        start_new_session=True
    )

    # 4. 啟動 cloudflared 加密隧道 (優先檢查是否有自訂固定 Token)
    cf_token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "").strip()
    if cf_token:
        cf_cmd = ["cloudflared", "tunnel", "run", "--token", cf_token]
        print(f"🔒 正在以固定 Named Tunnel Token 啟動...")
    else:
        # 使用 http2 協定加固模式，防範 macOS Wi-Fi 睡眠喚醒時 UDP/QUIC 斷線
        cf_cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", "http://localhost:8888"]

    cf_proc = subprocess.Popen(
        cf_cmd,
        cwd=str(BASE_DIR),
        stdout=fd_cf,
        stderr=subprocess.STDOUT,
        close_fds=False,
        start_new_session=True
    )

    print("⏳ 正在建立並確認 Cloudflare 隧道連線...")
    active_url = extract_active_url(log_cf_path, max_wait=12)

    # 將有效網址持久化存檔於 docs/ACTIVE_URL.txt
    active_url_file = BASE_DIR / "docs" / "ACTIVE_URL.txt"
    if active_url:
        with open(active_url_file, "w", encoding="utf-8") as f:
            f.write(f"PUBLIC_URL={active_url}\nUPDATED_AT={time.ctime()}\n")

    print("=" * 60)
    print("✅ 常駐守護進程已成功啟動！")
    print(f"  - Web Portal PID: {web_proc.pid} (監聽 Port 8888)")
    print(f"  - Cloudflare PID: {cf_proc.pid}")
    print(f"  - 本機網址: http://localhost:8888")
    if active_url:
        print(f"  - 🌐 Cloudflare 公網網址: {active_url}")
        print(f"  - 📄 網址已同步存檔至: {active_url_file}")
    else:
        print(f"  - 🌐 Cloudflare 正在初始化，請稍候 3 秒後開啟")
    print("=" * 60)

if __name__ == "__main__":
    main()

