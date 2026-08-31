"""
IBM FlashSystem 專家系統 - 系統設定檔
包含 Ollama 模型設定、檔案路徑、切片參數與 Web Portal 服務 Port
"""

import os
from pathlib import Path

# 專案根目錄 (位於 Google Drive)
BASE_DIR = Path(__file__).resolve().parent

# 資料夾與檔案路徑定義
RAW_DATA_DIR = BASE_DIR / "raw_data"
RAW_PDF_DIR = RAW_DATA_DIR / "pdfs"
RAW_URLS_FILE = RAW_DATA_DIR / "web_urls.txt"
MANIFEST_FILE = BASE_DIR / "manifest.json"
GLOBAL_VISITED_URLS_FILE = RAW_DATA_DIR / "global_visited_urls.json"
GLOBAL_CONTENT_HASHES_FILE = RAW_DATA_DIR / "global_content_hashes.json"

# 為避免 Google Drive 雲端同步時鎖定 SQLite/HNSW 向量資料庫檔案 (File Locking)，
# 將 Vector DB 與提取圖片儲存路徑移至本機使用者家目錄下
LOCAL_DATA_DIR = Path.home() / ".ibm_flashsystem_kb"
EXTRACTED_IMAGES_DIR = LOCAL_DATA_DIR / "extracted_images"
VECTOR_DB_DIR = LOCAL_DATA_DIR / "vector_db"

# 自動建立所需目錄
for directory in [RAW_DATA_DIR, RAW_PDF_DIR, LOCAL_DATA_DIR, EXTRACTED_IMAGES_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 自動解析 .env 檔案 (支援專案根目錄與 ~/.ibm_flashsystem_kb/.env)
for env_file in [BASE_DIR / ".env", LOCAL_DATA_DIR / ".env"]:
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

# Ollama API 服務設定
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Google Gemini 專家模型設定 (方案 A - Agentic Mode)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # 可選: "gemini", "ollama"

# 本地模型名稱設定
EMBEDDING_MODEL = "nomic-embed-text"     # 文字向量化模型
LLM_MODEL = "llama3.2:latest"            # 本地備用推理模型
VISION_MODEL = "llama3.2-vision"         # 本地多模態技術圖表解析模型

# 雲端入口 Web Portal 伺服器設定
PORTAL_PORT = int(os.getenv("PORTAL_PORT", "8888"))
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")









# 文本切片參數 (Chunking Configuration)
CHUNK_SIZE = 800         # 每個 Chunk 的字元數
CHUNK_OVERLAP = 150      # 重疊字元數以保持前後語意銜接

# 圖片過濾與解析設定
MIN_IMAGE_WIDTH = 150    # 過濾過小的圖解或圖標
MIN_IMAGE_HEIGHT = 150
