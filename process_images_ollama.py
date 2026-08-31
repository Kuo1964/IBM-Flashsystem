"""
IBM FlashSystem 官方手冊 - 純本地 Ollama 離線技術圖表解析工具 (process_images_ollama.py)
【嚴格遵循安全規範】：100% 純本地 Ollama 離線運作，絕不調用任何外部雲端 API
支援智慧品質門檻精煉 (Top-6核心大圖/本)、詳細錯誤診斷與 100% 斷點續傳
"""
import io
import json
import time
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, List
import fitz
from PIL import Image
import httpx

import config
from vector_store import add_chunks_to_db

IMAGE_MANIFEST_FILE = config.RAW_DATA_DIR / "image_manifest.json"
IMAGE_DIR = config.EXTRACTED_IMAGES_DIR

def load_image_manifest() -> Dict[str, Any]:
    if IMAGE_MANIFEST_FILE.exists():
        try:
            with open(IMAGE_MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_image_manifest(data: Dict[str, Any]):
    try:
        with open(IMAGE_MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[警告] 儲存 image_manifest 失敗: {e}")

def extract_quality_images_from_pdf(pdf_path: Path, max_per_pdf: int = 6) -> List[Dict[str, Any]]:
    """智慧品質門檻：嚴格篩選高價值核心架構圖、控制節點配置與後面板接線圖"""
    pdf_name = pdf_path.stem
    target_dir = IMAGE_DIR / pdf_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    candidates = []
    try:
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                actual_page = page_num + 1
                try:
                    images = doc[page_num].get_images(full=True)
                except Exception:
                    continue

                for img_idx, img_info in enumerate(images):
                    try:
                        xref = img_info[0]
                        base_img = doc.extract_image(xref)
                        if not base_img or "image" not in base_img:
                            continue
                        
                        img_bytes = base_img["image"]
                        if len(img_bytes) < 40 * 1024:  # 排除低於 40KB
                            continue

                        with Image.open(io.BytesIO(img_bytes)) as pil_img:
                            w, h = pil_img.size
                            ratio = max(w, h) / max(min(w, h), 1)

                            if w >= 450 and h >= 300 and ratio <= 3.0:
                                candidates.append({
                                    "xref": xref,
                                    "page": actual_page,
                                    "idx": img_idx,
                                    "bytes": img_bytes,
                                    "pil": pil_img,
                                    "size_score": w * h * len(img_bytes)
                                })
                    except Exception:
                        continue
    except Exception as e:
        print(f"[警告] 讀取 PDF 失敗 ({pdf_path.name}): {e}")

    candidates.sort(key=lambda x: x["size_score"], reverse=True)
    selected = candidates[:max_per_pdf]

    extracted = []
    for item in selected:
        actual_page = item["page"]
        img_idx = item["idx"]
        img_filename = f"page_{actual_page}_img_{img_idx}.jpg"
        save_path = target_dir / img_filename
        if not save_path.exists():
            rgb_img = item["pil"].convert("RGB")
            rgb_img.save(save_path, "JPEG", quality=92)

        w, h = item["pil"].size
        extracted.append({
            "image_id": f"{pdf_name}_p{actual_page}_img{img_idx}",
            "image_path": str(save_path),
            "pdf_name": pdf_name,
            "page_number": actual_page,
            "width": w,
            "height": h
        })
        
    return extracted

def generate_ollama_vision_summary(image_path: str, model_name: str = "llama3.2-vision") -> tuple[str, str]:
    """100% 純本地 Ollama 視覺模型調用 (絕不連外)"""
    try:
        with open(image_path, "rb") as f:
            base64_str = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "你是一位 IBM FlashSystem 資深儲存硬體架構師。\n"
            "請仔細分析這張提取自官方技術手冊的硬體圖表，說明：\n"
            "1. 組件名稱與用途 (如 Node Canister, PCIe Slot, Power Supply, Drive Bay, Host Interface Card)\n"
            "2. 連接埠與架構特徵 (如 10/25GbE RoCE, 32Gb FC, SAS 擴充埠, 燈號狀態)\n"
            "請以繁體中文給出清晰的技術描述摘要與關鍵字清單。"
        )

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "images": [base64_str]
        }

        res = httpx.post(f"{config.OLLAMA_HOST}/api/generate", json=payload, timeout=90.0)
        if res.status_code == 200:
            summary = res.json().get("response", "").strip()
            if summary:
                return summary, f"Ollama ({model_name})"
            return "", f"Ollama ({model_name}) 回傳空字串"
        elif res.status_code == 500 and "unknown model architecture" in res.text:
            return "", f"Ollama 版本過舊，不支援 '{model_name}' (mllama) 架構。\n   👉 解決方法 1: 請執行 brew upgrade ollama 升級\n   👉 解決方法 2: 切換相容模型 python process_images_ollama.py --model llava"
        elif res.status_code == 404:
            return "", f"Ollama 找不到模型 '{model_name}' (請在終端機執行: ollama pull {model_name})"
        else:
            return "", f"Ollama 錯誤 (HTTP {res.status_code}): {res.text[:120]}"
            
    except httpx.ConnectError:
        return "", f"無法連線至 Ollama 服務 ({config.OLLAMA_HOST})，請確認是否已啟動 ollama"
    except Exception as e:
        return "", f"Ollama 本地推理異常: {e}"

def run_vision_harvester(ollama_model: str = "llama3.2-vision"):
    print("=" * 70)
    print(f"🖼️ 啟動純本地 Ollama 離線技術圖表解析引擎 (模型: {ollama_model})")
    print("🔒 安全保證: 100% 純本機運作，絕不連線任何外部雲端 API")
    print("=" * 70)

    image_manifest = load_image_manifest()
    pdf_files = list(config.RAW_PDF_DIR.glob("*.pdf")) + list(config.RAW_PDF_DIR.glob("*.PDF"))
    print(f"📂 正在掃描 {len(pdf_files)} 本手冊，精選核心架構圖...")

    all_candidate_images = []
    for pdf_path in pdf_files:
        imgs = extract_quality_images_from_pdf(pdf_path, max_per_pdf=6)
        all_candidate_images.extend(imgs)

    print(f"📊 通過精選門檻之高價值核心圖表共: {len(all_candidate_images)} 張")

    processed = 0
    skipped = 0

    for i, img_rec in enumerate(all_candidate_images, 1):
        img_id = img_rec["image_id"]
        
        # 斷點續傳檢查
        if img_id in image_manifest and image_manifest[img_id].get("status") == "success":
            skipped += 1
            continue

        print(f"\n[{i}/{len(all_candidate_images)}] 🔍 正在本地分析: {img_rec['pdf_name']} (第 {img_rec['page_number']} 頁) ...", end=" ", flush=True)
        t0 = time.time()
        
        summary, engine_used = generate_ollama_vision_summary(img_rec["image_path"], model_name=ollama_model)
        cost = time.time() - t0
        
        if summary:
            # 建立圖片 Chunk 並寫入 SQLite
            chunk = {
                "chunk_id": f"img_{img_id}",
                "text": f"【IBM FlashSystem 技術圖表 - {img_rec['pdf_name']} 第 {img_rec['page_number']} 頁】\n{summary}",
                "metadata": {
                    "source": img_rec["pdf_name"],
                    "page": img_rec["page_number"],
                    "type": "image",
                    "image_path": img_rec["image_path"],
                    "image_id": img_id
                }
            }
            add_chunks_to_db([chunk])

            # 記錄斷點 Manifest
            image_manifest[img_id] = {
                "status": "success",
                "pdf": img_rec["pdf_name"],
                "page": img_rec["page_number"],
                "path": img_rec["image_path"],
                "summary_len": len(summary),
                "engine": engine_used
            }
            save_image_manifest(image_manifest)
            processed += 1
            print(f"✅ 完成 [{engine_used}] (耗時 {cost:.1f}s, 摘要 {len(summary)} 字)")
        else:
            print(f"❌ 失敗: {engine_used}")
            # 如果是架構或連線錯誤，在第 1 次失敗時立即停止，避免無限重試
            if "unknown model architecture" in engine_used or "無法連線" in engine_used or "找不到模型" in engine_used:
                print(f"\n💡 【本地 Ollama 故障排除指引】:")
                print(f"   {engine_used}\n")
                break

        time.sleep(0.5)

    print("\n" + "=" * 70)
    print(f"🎉 本地技術圖表解析任務結束！")
    print(f"   - 本次新增解析: {processed} 張圖表")
    print(f"   - 斷點已存在略過: {skipped} 張圖表")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IBM FlashSystem 純本地 Ollama 視覺解析工具")
    parser.add_argument("--model", default="llama3.2-vision", help="指定本地 Ollama 視覺模型 (預設: llama3.2-vision, 可選: llava)")
    args = parser.parse_args()

    run_vision_harvester(ollama_model=args.model)
