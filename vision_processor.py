"""
IBM FlashSystem 專家系統 - 多模態圖表摘要解析器
呼叫 Ollama 本地視覺模型 (llama3.2-vision) 為提取出之技術圖表生成繁體中文摘要與關鍵字
"""

import base64
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
import config

def encode_image_to_base64(image_path: str) -> str:
    """將圖片檔案轉為 Base64 字串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_image_summary(image_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    呼叫 Ollama 本地 Vision 模型解析技術圖表
    返回包含圖表摘要與元資料的 Chunk 物件
    """
    image_path = image_record["image_path"]
    pdf_name = image_record["pdf_name"]
    page_number = image_record["page_number"]
    image_id = image_record["image_id"]

    prompt = (
        "這是一張提取自 IBM FlashSystem 技術紅皮書 (Redbook) 的技術圖表。\n"
        "請仔細分析圖中的組件、連接關係（如 SAN Switch、NVMe-oF、RAID 配置、控制器或介面卡）、數據流向或架構特徵。\n"
        "請生成一份繁體中文的技術描述摘要，並列出關鍵術語標籤。"
    )

    try:
        base64_image = encode_image_to_base64(image_path)
        payload = {
            "model": config.VISION_MODEL,
            "prompt": prompt,
            "stream": False,
            "images": [base64_image]
        }

        response = httpx.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=60.0
        )

        if response.status_code == 200:
            result = response.json()
            summary_text = result.get("response", "").strip()

            if summary_text:
                return {
                    "chunk_id": f"vision_{image_id}",
                    "text": f"[圖表摘要 - {pdf_name} 第 {page_number} 頁]\n{summary_text}",
                    "metadata": {
                        "source": pdf_name,
                        "page": page_number,
                        "type": "image_summary",
                        "image_path": image_path,
                        "image_id": image_id
                    }
                }
    except Exception as e:
        print(f"[警告] Vision 模型解析圖片失敗 ({image_id}): {e}")

    # 若 Vision 暫不可用，生成降級的圖案索引紀錄
    return {
        "chunk_id": f"vision_{image_id}",
        "text": f"[IBM FlashSystem 技術圖表] 來自紅皮書 {pdf_name} 第 {page_number} 頁之圖表結構。",
        "metadata": {
            "source": pdf_name,
            "page": page_number,
            "type": "image_summary",
            "image_path": image_path,
            "image_id": image_id
        }
    }
