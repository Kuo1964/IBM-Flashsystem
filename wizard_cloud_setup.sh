#!/usr/bin/env bash
# ==============================================================================
# IBM FlashSystem 專家系統 - 雲端入口 Web Portal 與 Cloudflare 一鍵部署嚮導 (Wizard)
# ==============================================================================
set -euo pipefail

TOTAL_STAGES=4
CURRENT_STAGE=0

# 色彩與視覺標籤
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

say() { echo -e "${CYAN}[Wizard]${NC} $1"; }
step() { echo -e "${GREEN}▸${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }

open_url() {
    local url="$1"
    say "正在為您開啟網頁: ${url}"
    if command -v open &>/dev/null; then
        open "$url"
    elif command -v xdg-open &>/dev/null; then
        xdg-open "$url"
    else
        say "請手動在瀏覽器打開網址: ${url}"
    fi
}

confirm() {
    local prompt_msg="$1"
    echo -e -n "${YELLOW}? ${prompt_msg} [Y/n]: ${NC}"
    read -r resp
    case "$resp" in
        [nN][oO]|[nN])
            say "操作已由使用者暫停。"
            exit 1
            ;;
        *)
            ;;
    esac
}

stage_header() {
    CURRENT_STAGE=$((CURRENT_STAGE + 1))
    clear || true
    echo -e "${MAGENTA}==============================================================================${NC}"
    echo -e "${MAGENTA} 🚀 IBM FlashSystem 雲端問答入口部署嚮導 (階段 ${CURRENT_STAGE} / ${TOTAL_STAGES})${NC}"
    echo -e "${MAGENTA}==============================================================================${NC}"
    echo ""
}

# ------------------------------------------------------------------------------
# 階段 1：檢查 Ollama 本地推理模型服務
# ------------------------------------------------------------------------------
stage_header
say "階段 1/4: 檢查 Ollama 本地推理服務狀態 (Embedding / LLM / Vision)"
step "正在測試本地 Ollama API (http://localhost:11434) ..."

if curl -s http://localhost:11434/api/tags &>/dev/null; then
    success "Ollama 服務正在正常運行中！"
else
    warn "未偵測到 Ollama 服務或服務未開啟！"
    step "請在終端機啟動 Ollama 應用程式，或執行: ollama serve"
    confirm "完成 Ollama 啟動後，按 Enter 繼續"
fi

# ------------------------------------------------------------------------------
# 階段 2：設定 Web Cloud Portal 連線 Port 與環境變數
# ------------------------------------------------------------------------------
stage_header
say "階段 2/4: 設定 Web Cloud Portal 服務 Port 與 IP 綁定"
step "建議 Port: 8888 (避開已佔用端口)"
echo -e -n "${CYAN}請輸入 Web Portal 欲使用的 Port [預設 8888]: ${NC}"
read -r input_port
PORT=${input_port:-8888}

step "設定環境變數 PORTAL_PORT=${PORT} ..."
export PORTAL_PORT="${PORT}"
success "Web Portal 監聽端口已設定為: ${PORT}"

# ------------------------------------------------------------------------------
# 階段 3：Cloudflare Tunnel 免費加密通道設定 (提供同仁公開/外網連線)
# ------------------------------------------------------------------------------
stage_header
say "階段 3/4: Cloudflare Tunnel 免費公網穿透與零信任身份防護設定"
step "說明：Cloudflare Tunnel 可讓外網/團隊同事連入本機，完全不需要開放路由器改 Port，且 100% 免費！"
echo ""
step "選項 1: 使用本機快速公網通道 (Quick Tunnel)"
step "選項 2: 開啟 Cloudflare Dashboard 自訂專屬安全域名"
step "選項 3: 僅內網存取 (Local & LAN Only)"
echo -e -n "${CYAN}請選擇 Cloudflare 通道模式 (1=Quick Tunnel / 2=自訂域名 / 3=僅內網存取) [預設 1]: ${NC}"
read -r cf_choice
cf_mode=${cf_choice:-1}

if [ "$cf_mode" = "1" ]; then
    if ! command -v cloudflared &>/dev/null; then
        say "偵測到未安裝 cloudflared 工具，正在嘗試透過 Homebrew 安裝..."
        brew install cloudflared || warn "請手動執行: brew install cloudflared"
    fi
    success "Cloudflare 環境已準備就緒！"
elif [ "$cf_mode" = "2" ]; then
    open_url "https://one.dash.cloudflare.com"
    step "請在 Cloudflare 儀表板點選 Access -> Tunnels -> Create Tunnel"
    step "將服務目標指向: http://localhost:${PORT}"
    confirm "完成 Cloudflare 儀表板設定後，按 Enter 繼續"
else
    say "跳過 Cloudflare 通道設定，將僅供本機與同公司內網連線 (http://localhost:${PORT})"
fi

# ------------------------------------------------------------------------------
# 階段 4：啟動 Web Portal 伺服器與 Cloudflare 通道
# ------------------------------------------------------------------------------
stage_header
say "階段 4/4: 啟動 IBM FlashSystem 專家系統 Web Cloud Portal"
step "正在啟動 Web 服務與 Cloudflare 常駐守護進程 (OS Session Leader) ..."

# 使用常駐守護腳本啟動
.venv/bin/python scripts/start_portal_daemon.py

echo ""
success "=============================================================================="
success "🎉 IBM FlashSystem 團隊專家系統 Web Cloud Portal 常駐守護已成功啟動！"
success "=============================================================================="
echo ""
say "📌 本機與內網同事存取網址: http://localhost:${PORT}"
say "📌 守護進程已脫離 Shell 限制，關閉此視窗服務依然會持續穩定在線！"
say "📌 如需停止服務，請執行: .venv/bin/python scripts/stop_portal_daemon.py"

