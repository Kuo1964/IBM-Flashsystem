"""
IBM FlashSystem 專家系統 - 雲端入口常駐守護進程關閉腳本
"""
import subprocess

def main():
    print("🛑 正在停止 IBM FlashSystem Web Portal 常駐進程與 Cloudflare 隧道...")
    subprocess.run(["lsof -ti :8888 | xargs kill -9 2>/dev/null || true"], shell=True)
    subprocess.run(["pkill -9 cloudflared 2>/dev/null || true"], shell=True)
    print("✅ 已成功安全關閉所有常駐進程！")

if __name__ == "__main__":
    main()
