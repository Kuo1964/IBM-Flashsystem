"""
IBM FlashSystem 專家系統 - 系統設定檔
包含 Ollama 模型設定、檔案路徑與切片參數
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

# 為避免 Google Drive 雲端同步時鎖定 SQLite/HNSW 向量資料庫檔案 (File Locking)，
# 將 Vector DB 儲存路徑移至本機使用者家目錄下
LOCAL_DATA_DIR = Path.home() / ".ibm_flashsystem_kb"
EXTRACTED_IMAGES_DIR = LOCAL_DATA_DIR / "extracted_images"
VECTOR_DB_DIR = LOCAL_DATA_DIR / "vector_db"

# 自動建立所需目錄
for directory in [RAW_DATA_DIR, RAW_PDF_DIR, LOCAL_DATA_DIR, EXTRACTED_IMAGES_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Ollama API 服務設定
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


# Ollama 模型名稱設定
EMBEDDING_MODEL = "nomic-embed-text"     # 文字向量化模型
LLM_MODEL = "llama3.2:latest"            # 本地文字解答與推理模型
VISION_MODEL = "llama3.2-vision"         # 本地多模態技術圖表解析模型

# 文本切片參數 (Chunking Configuration)
CHUNK_SIZE = 800         # 每個 Chunk 的字元數
CHUNK_OVERLAP = 150      # 重疊字元數以保持前後語意銜接

# 圖片過濾與解析設定
MIN_IMAGE_WIDTH = 150    # 過濾過小的圖解或圖標
MIN_IMAGE_HEIGHT = 150
